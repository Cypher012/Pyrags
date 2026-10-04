from datetime import UTC, datetime

SAMPLE_BASE_TIME = datetime(2026, 10, 2, 17, 55, 51, tzinfo=UTC)

SAMPLE_FILES = (
    "Introduction to Machine Learning.pdf",
    "Research Methods Handbook.pdf",
    "Database Systems Lecture Notes.pdf",
    "Distributed Systems Overview.pdf",
    "Neural Networks Study Guide.pdf",
    "Software Architecture Notes.docx",
    "Cloud Computing Fundamentals.pdf",
    "Natural Language Processing.pdf",
    "Data Structures and Algorithms.pdf",
    "Computer Networks Handbook.pdf",
    "Statistics for Research.pdf",
    "Information Retrieval Notes.docx",
    "Human Computer Interaction.pdf",
    "Operating Systems Review.pdf",
    "Cybersecurity Fundamentals.pdf",
    "Academic Writing Guide.docx",
    "Applied Linear Algebra.pdf",
    "Ethics in Artificial Intelligence.pdf",
    "Project Planning Notes.docx",
    "Advanced Python Patterns.pdf",
)

SAMPLE_DOCUMENT_COUNTS = (
    2, 4, 3, 6, 5, 7, 2, 8, 4, 3,
    6, 5, 7, 2, 8, 4, 3, 6, 5, 7,
)

SAMPLE_SOURCE_CONTENT = "Sample citation content for frontend testing; no document was retrieved."

SAMPLE_MESSAGES = (
    ("user", "Can you summarize this document?"),
    ("assistant", "This is a sample summary for the mock conversation."),
    ("user", "What are the main points?"),
    ("assistant", "The mock document covers an introduction, key ideas, and examples."),
    ("user", "Can you explain the first idea?"),
    ("assistant", "The first idea introduces the topic and why it matters."),
    ("user", "Does the document include an example?"),
    ("assistant", "Yes. It includes a simple example to illustrate the idea."),
    ("user", "What should I remember for revision?"),
    ("assistant", "Focus on the definitions, main ideas, and example."),
    ("user", "Can you give me a short conclusion?"),
    ("assistant", "The document connects its key ideas to a practical use case."),
)
