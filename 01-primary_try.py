import json
import csv
import os
from typing import Dict, Optional
from llm_hub import deepseek_chat  # Assuming this is your LLM API wrapper

# Evaluation schema (extensible for other subjects)
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
    # Add more subjects here, e.g., "数学": {...}
}

# Prompt template (extensible for other subjects)
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
        self.students = {}  # {student_id: {name, scores}}
        self.load_students()
        self.load_scores()

    def load_students(self):
        """Load student list from CSV."""
        if os.path.exists(self.csv_file):
            with open(self.csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.students[row["student_id"]] = {
                        "name": row["name"],
                        "scores": {}
                    }
        else:
            # Create default student list if CSV doesn't exist
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
        """Save student list to CSV."""
        with open(self.csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["student_id", "name"])
            writer.writeheader()
            for student_id, info in self.students.items():
                writer.writerow({"student_id": student_id, "name": info["name"]})

    def load_scores(self):
        """Load score records from JSON."""
        if os.path.exists(self.json_file):
            with open(self.json_file, "r", encoding="utf-8") as f:
                scores_data = json.load(f)
                for student_id, subjects in scores_data.items():
                    if student_id in self.students:
                        self.students[student_id]["scores"] = subjects

    def save_scores(self):
        """Save score records to JSON."""
        scores_data = {sid: info["scores"] for sid, info in self.students.items()}
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(scores_data, f, ensure_ascii=False, indent=2)

    def add_student(self, student_id: str, name: str):
        """Add a new student."""
        if student_id not in self.students:
            self.students[student_id] = {"name": name, "scores": {}}
            self.save_students()

    def update_scores(self, student_id: str, subject: str, scores: Dict):
        """Update student scores."""
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} does not exist")
        if subject not in self.students[student_id]["scores"]:
            self.students[student_id]["scores"][subject] = []
        self.students[student_id]["scores"][subject].append(scores)
        self.save_scores()

    def get_latest_scores(self, student_id: str, subject: str) -> Optional[Dict]:
        """Get the latest scores for a student."""
        if (student_id in self.students and
                subject in self.students[student_id]["scores"] and
                self.students[student_id]["scores"][subject]):
            return self.students[student_id]["scores"][subject][-1]
        return None

    def get_previous_scores(self, student_id: str, subject: str) -> Optional[Dict]:
        """Get the previous scores for a student."""
        if (student_id in self.students and
                subject in self.students[student_id]["scores"] and
                len(self.students[student_id]["scores"][subject]) > 1):
            return self.students[student_id]["scores"][subject][-2]
        return None

class FeedbackGenerator:
    def __init__(self, schema: Dict):
        self.schema = schema

    def format_score_details(self, scores: Dict, previous_scores: Optional[Dict]) -> str:
        """Format score details for the prompt."""
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
        """Generate feedback description."""
        previous_scores = db.get_previous_scores(student_id, subject)
        score_details = self.format_score_details(scores, previous_scores)
        prompt = PROMPT_TEMPLATE.format(subject=subject, score_details=score_details)
        feedback = deepseek_chat(user_prompt=prompt)
        return feedback

def main():
    # Initialize database and feedback generator
    db = StudentDatabase()
    generator = FeedbackGenerator(EVALUATION_SCHEMA)

    # Example scores (first evaluation)
    scores1 = {
        "专业模块": {
            "古文": {"字词理解": 4, "句式分析": 3, "篇章理解": 2},
            "现代文": {"记叙文阅读": 3, "说明文阅读": 4, "议论文阅读": 3},
            "写作": {"素材积累": 2, "结构组织": 3, "语言表达": 3},
            "诗歌": {"意象理解": 3, "情感分析": 4, "技巧掌握": 3}
        },
        "学习习惯": {
            "课堂专注度": 4,
            "作业完成质量": 3,
            "复习主动性": 2
        },
        "学生能力": {
            "答题速度": 3,
            "正确率": 4,
            "细心程度": 3
        }
    }
    student_id = "002"
    subject = "语文"
    db.update_scores(student_id, subject, scores1)
    feedback = generator.generate_feedback(student_id, subject, scores1, db)
    print("第一次反馈：")
    print(feedback)

    # Example scores (second evaluation, uncomment to test)
    scores2 = {
        "专业模块": {
            "古文": {"字词理解": 5, "句式分析": 3, "篇章理解": 3},
            "现代文": {"记叙文阅读": 4, "说明文阅读": 4, "议论文阅读": 3},
            "写作": {"素材积累": 3, "结构组织": 4, "语言表达": 3},
            "诗歌": {"意象理解": 4, "情感分析": 4, "技巧掌握": 4}
        },
        "学习习惯": {
            "课堂专注度": 4,
            "作业完成质量": 4,
            "复习主动性": 3
        },
        "学生能力": {
            "答题速度": 4,
            "正确率": 4,
            "细心程度": 4
        }
    }
    db.update_scores(student_id, subject, scores2)
    feedback = generator.generate_feedback(student_id, subject, scores2, db)
    print("\n第二次反馈（对比前次）：")
    print(feedback)

if __name__ == "__main__":
    main()