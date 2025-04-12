import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Optional
from llm_hub import deepseek_chat  # Replace with your LLM API if needed

# Evaluation schema (loaded from JSON)
if os.path.exists("EVALUATION_SCHEMA.json"):
    with open("EVALUATION_SCHEMA.json", "r", encoding="utf-8") as f:
        EVALUATION_SCHEMA = json.load(f)
else:
    EVALUATION_SCHEMA = {
        "语文": {
            "专业模块": {
                "古文": ["字词理解", "句式分析", "篇章理解"],
                "现代文": ["记叙文阅读", "说明文阅读", "议论文阅读"],
                "写作": ["素材积累", "结构组织", "语言表达"],
                "诗歌": ["意象理解", "情感分析", "技巧掌握"]
            },
            "学习习惯": ["课堂专注度", "作业完成质量", "复习主动性"],
            "学生能力": ["答题速度", "正确率", "细心程度"]
        }
    }
    with open("EVALUATION_SCHEMA.json", "w", encoding="utf-8") as f:
        json.dump(EVALUATION_SCHEMA, f, ensure_ascii=False, indent=2)

# Prompt template
PROMPT_TEMPLATE = """
你是一位{subject}老师，根据学生的评价分数生成“近期学习水平及状态反馈”。以下是学生的打分（5分制，5为优秀，1为较差）：

{score_details}

请根据这些分数，为学生生成一段结构化的反馈描述，格式如下：

**{subject}近期学习水平及状态反馈**

**专业模块**
- 古文：...
- 现代文：...
- 写作：...
- 诗歌：...

**学习习惯**
- ...

**学生能力**
- ...

要求：
1. 反馈语言需简洁、客观、鼓励性，适合学生和家长阅读。
2. 根据分数高低（5-4为优秀，3为中等，2-1为需改进），描述学生的表现，并提出改进建议。
3. 如果有分数变化（与上次相比），突出进步或需要关注的退步。
4. 每项反馈控制在1-2句话。

请严格按照格式输出。
"""

class StudentDatabase:
    def __init__(self, csv_file: str = "students.csv", json_file: str = "scores.json"):
        self.csv_file = csv_file
        self.json_file = json_file
        self.students = {}
        self.load_students()
        self.load_scores()

    def load_students(self):
        if os.path.exists(self.csv_file):
            df = pd.read_csv(self.csv_file)
            for _, row in df.iterrows():
                self.students[str(row["student_id"])] = {
                    "name": row["name"],
                    "scores": {}
                }
        else:
            default_students = [
                {"student_id": "001", "name": "张伟"},
                {"student_id": "002", "name": "李娜"},
                {"student_id": "003", "name": "王芳"},
                {"student_id": "004", "name": "刘洋"},
                {"student_id": "005", "name": "陈晨"},
                {"student_id": "006", "name": "杨磊"},
                {"student_id": "007", "name": "赵静"},
                {"student_id": "008", "name": "周浩"}
            ]
            self.students = {s["student_id"]: {"name": s["name"], "scores": {}} for s in default_students}
            self.save_students()

    def save_students(self):
        df = pd.DataFrame([
            {"student_id": sid, "name": info["name"]}
            for sid, info in self.students.items()
        ])
        df.to_csv(self.csv_file, index=False, encoding="utf-8")

    def load_scores(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as f:
                scores_data = json.load(f)
                for student_id, subjects in scores_data.items():
                    if student_id in self.students:
                        self.students[student_id]["scores"] = subjects

    def save_scores(self):
        scores_data = {sid: info["scores"] for sid, info in self.students.items()}
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(scores_data, f, ensure_ascii=False, indent=2)

    def add_student(self, student_id: str, name: str):
        if student_id not in self.students:
            self.students[student_id] = {"name": name, "scores": {}}
            self.save_students()

    def update_scores(self, student_id: str, subject: str, scores: Dict):
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} does not exist")
        if subject not in self.students[student_id]["scores"]:
            self.students[student_id]["scores"][subject] = []
        self.students[student_id]["scores"][subject].append(scores)
        self.save_scores()

    def get_latest_scores(self, student_id: str, subject: str) -> Optional[Dict]:
        if (student_id in self.students and
                subject in self.students[student_id]["scores"] and
                self.students[student_id]["scores"][subject]):
            return self.students[student_id]["scores"][subject][-1]
        return None

    def get_previous_scores(self, student_id: str, subject: str) -> Optional[Dict]:
        if (student_id in self.students and
                subject in self.students[student_id]["scores"] and
                len(self.students[student_id]["scores"][subject]) > 1):
            return self.students[student_id]["scores"][subject][-2]
        return None

class FeedbackGenerator:
    def __init__(self, schema: Dict):
        self.schema = schema

    def format_score_details(self, scores: Dict, previous_scores: Optional[Dict]) -> str:
        details = []
        for category, subcategories in self.schema["语文"].items():
            details.append(f"{category}：")
            if isinstance(subcategories, dict):
                for subcategory, items in subcategories.items():
                    for item in items:
                        current_score = scores.get(category, {}).get(subcategory, {}).get(item, 3)
                        prev_score = (previous_scores.get(category, {}).get(subcategory, {}).get(item, None)
                                     if previous_scores else None)
                        line = f"- {item}：{current_score}/5"
                        if prev_score is not None:
                            change = "进步" if current_score > prev_score else "下降" if current_score < prev_score else "持平"
                            line += f"（与上次相比：{change}）"
                        details.append(line)
            elif isinstance(subcategories, list):
                for item in subcategories:
                    current_score = scores.get(category, {}).get(item, 3)
                    prev_score = (previous_scores.get(category, {}).get(item, None)
                                 if previous_scores else None)
                    line = f"- {item}：{current_score}/5"
                    if prev_score is not None:
                        change = "进步" if current_score > prev_score else "下降" if current_score < prev_score else "持平"
                        line += f"（与上次相比：{change}）"
                    details.append(line)
        return "\n".join(details)

    def generate_feedback(self, student_id: str, subject: str, scores: Dict, db: StudentDatabase) -> str:
        previous_scores = db.get_previous_scores(student_id, subject)
        score_details = self.format_score_details(scores, previous_scores)
        prompt = PROMPT_TEMPLATE.format(subject=subject, score_details=score_details)
        feedback = deepseek_chat(user_prompt=prompt)
        return feedback

# Streamlit App
st.set_page_config(page_title="学生评价系统", layout="wide")

# Sidebar
st.sidebar.title("学科选择")
subject = st.sidebar.selectbox("选择学科", list(EVALUATION_SCHEMA.keys()), index=0)

# Initialize database and feedback generator
db = StudentDatabase()
generator = FeedbackGenerator(EVALUATION_SCHEMA)

# Multi-page navigation
page = st.sidebar.radio("导航", ["介绍", "学生信息", "学生能力展示", "问卷填写", "报告生成"])

if page == "介绍":
    st.title("学生评价系统介绍")
    st.markdown("""
    欢迎使用学生评价系统！本系统旨在帮助教师评估学生的学习水平和状态，并生成结构化的反馈报告。主要功能包括：

    - **学生信息管理**：查看和编辑学生名单。
    - **学生能力展示**：通过雷达图直观展示学生能力。
    - **问卷填写**：为学生录入评价分数，基于预定义的评价维度。
    - **报告生成**：根据评价分数生成反馈报告，分析进步或需要改进的方面。

    使用左侧导航栏选择学科和页面开始操作！
    """)

elif page == "学生信息":
    st.title("学生信息管理")
    st.subheader("学生名单")

    # Load and display student data
    students_df = pd.DataFrame([
        {"student_id": sid, "name": info["name"]}
        for sid, info in db.students.items()
    ])
    st.dataframe(students_df, use_container_width=True)

    # Add new student
    st.subheader("添加新学生")
    with st.form("add_student_form"):
        new_id = st.text_input("学号")
        new_name = st.text_input("姓名")
        submit = st.form_submit_button("添加")
        if submit and new_id and new_name:
            db.add_student(new_id, new_name)
            st.success(f"已添加学生 {new_name} (学号: {new_id})")
            st.rerun()

    # Edit existing student
    st.subheader("编辑学生信息")
    student_ids = list(db.students.keys())
    if student_ids:
        edit_id = st.selectbox("选择学生", student_ids, key="edit_student")
        current_name = db.students[edit_id]["name"]
        with st.form("edit_student_form"):
            updated_name = st.text_input("姓名", value=current_name)
            submit_edit = st.form_submit_button("更新")
            if submit_edit and updated_name:
                db.students[edit_id]["name"] = updated_name
                db.save_students()
                st.success(f"已更新学生 {edit_id} 的姓名为 {updated_name}")
                st.rerun()

elif page == "学生能力展示":
    st.title("学生能力展示")
    student_names = [info["name"] for info in db.students.values()]
    if student_names:
        selected_name = st.selectbox("选择学生", student_names)
        selected_id = next(sid for sid, info in db.students.items() if info["name"] == selected_name)
        scores = db.get_latest_scores(selected_id, subject)
        
        if scores and "学生能力" in scores:
            abilities = scores["学生能力"]
            labels = list(abilities.keys())
            values = list(abilities.values())
            
            # Create radar chart
            fig = go.Figure(data=go.Scatterpolar(
                r=values + [values[0]],  # Close the loop
                theta=labels + [labels[0]],
                fill='toself'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                showlegend=False,
                title=f"{selected_name} 的学生能力"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("该学生暂无能力评价数据。")
    else:
        st.warning("暂无学生数据。")

elif page == "问卷填写":
    st.title("学生评价问卷")
    student_names = [info["name"] for info in db.students.values()]
    if student_names:
        selected_name = st.selectbox("选择学生", student_names, key="eval_student")
        selected_id = next(sid for sid, info in db.students.items() if info["name"] == selected_name)
        
        st.subheader("评价维度")
        scores = {}
        with st.form("evaluation_form"):
            for category, subcategories in EVALUATION_SCHEMA[subject].items():
                scores[category] = {}
                st.markdown(f"**{category}**")
                if isinstance(subcategories, dict):
                    for subcategory, items in subcategories.items():
                        st.markdown(f"*{subcategory}*")
                        scores[category][subcategory] = {}
                        for item in items:
                            score = st.slider(f"{item}", 1, 5, 3, key=f"{selected_id}_{category}_{subcategory}_{item}")
                            scores[category][subcategory][item] = score
                elif isinstance(subcategories, list):
                    for item in subcategories:
                        score = st.slider(f"{item}", 1, 5, 3, key=f"{selected_id}_{category}_{item}")
                        scores[category][item] = score
            submit_scores = st.form_submit_button("提交评价")
            
            if submit_scores:
                # Save to scores_new.json
                scores_new = {}
                if os.path.exists("scores_new.json"):
                    with open("scores_new.json", "r", encoding="utf-8") as f:
                        scores_new = json.load(f)
                if selected_id not in scores_new:
                    scores_new[selected_id] = {}
                if subject not in scores_new[selected_id]:
                    scores_new[selected_id][subject] = []
                scores_new[selected_id][subject].append(scores)
                with open("scores_new.json", "w", encoding="utf-8") as f:
                    json.dump(scores_new, f, ensure_ascii=False, indent=2)
                st.success(f"已为 {selected_name} 保存评价数据！")
    else:
        st.warning("暂无学生数据。")

elif page == "报告生成":
    st.title("反馈报告生成")
    student_names = [info["name"] for info in db.students.values()]
    if student_names:
        selected_name = st.selectbox("选择学生", student_names, key="report_student")
        selected_id = next(sid for sid, info in db.students.items() if info["name"] == selected_name)
        
        # Load latest scores from scores_new.json
        scores_new = {}
        if os.path.exists("scores_new.json"):
            with open("scores_new.json", "r", encoding="utf-8") as f:
                scores_new = json.load(f)
        
        if (selected_id in scores_new and
                subject in scores_new[selected_id] and
                scores_new[selected_id][subject]):
            latest_scores = scores_new[selected_id][subject][-1]
            if st.button("生成反馈报告"):
                feedback = generator.generate_feedback(selected_id, subject, latest_scores, db)
                st.markdown(f"**{selected_name} 的反馈报告**")
                st.write(feedback)
                
                # Update scores.json
                db.update_scores(selected_id, subject, latest_scores)
                st.success("已更新学生评价数据到 scores.json")
        else:
            st.warning("该学生暂无最新评价数据，请先填写问卷。")
    else:
        st.warning("暂无学生数据。")