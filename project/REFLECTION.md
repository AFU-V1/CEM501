# REFLECTION.md

## What I Built

This project is a communication assistant for project engineers. It reads emails and Telegram messages (texts, voices, images), classifies their urgency, summarizes content, and generates draft replies using LLM. The system stores communication history, supports daily reports and digests, and requires human approval before sending any response. Its goal is to reduce communication workload and improve project communication efficiency. As an additional feature, the agent also supports Telegram voice messages and images. Site teams can send short updates through Telegram, and the system can understand the message, classify its importance, and prepare a suitable response or daily report input.

## Communication Lessons

Building this agent taught me that professional CEM communication is not only about writing clearly, but also about understanding urgency, responsibility, and possible consequences. In construction projects, even a short email can affect cost, schedule, safety, or contractual rights. For example, a delay notice, an RFI, or a safety warning must be classified correctly because each one requires a different response time and tone. I also learned that the sender's role matters. A message from the owner, consultant, subcontractor, or site engineer may require different wording and level of formality. The agent helped me think more carefully about deadlines, action items, and who is responsible for the next step. Most importantly, I understood why human approval is necessary before sending responses, because an incorrect sentence may create legal or financial risk.

## AI-Assisted Development Lessons

I used AI coding tools as a director, not only as a source of code. First, I defined the project goal, the required modules, and the construction communication scenario. AI helped me generate draft functions, improve the dashboard structure, write sample data, and create clearer documentation. However, I had to review and correct the outputs because some suggestions did not match my project architecture or the course requirements. For example, I checked whether the agent still had email reading, urgency triage, OpenAI draft generation, human approval, SQLite memory, scheduler, digest/report builder, and dashboard functions. I also debugged integration issues and made sure the system did not send messages without approval. To control the process, I compared the final structure with the course milestones and adjusted the implementation according to those expectations.

## What I'd Do Differently

Although the agent works as a functional prototype, it still has some limitations. Attachment handling can be improved. In real construction communication, drawings, photos, RFIs, and reports are often sent as attachments, so the system should analyze them more effectively.

## Connection to Professional Practice

This project is closely related to future construction management work because communication is one of the main responsibilities of a project engineers. In real projects, engineers receive many RFIs, submittal updates, safety notices, delay notices, and messages from clients, consultants, and subcontractors. Missing or misunderstanding one message can create cost, schedule, quality, or safety problems. This agent can support the project engineer by organizing messages, identifying urgent issues, preparing draft responses, and helping follow up on open action items. For example, it can make RFI and submittal tracking easier and help ensure that delay or safety notices are not ignored. However, human approval is still essential.
