---
number-sections: false
format:
  html:
    number-sections: false
---

# Preface {.unnumbered}

This book exists because the accounting profession has changed faster than most accounting curricula have adapted. Organizations now generate financial and operational data at a scale that makes traditional manual methods of analysis insufficient. Enterprise resource planning systems capture every transaction, every journal entry, every payment, and every production order in relational databases that contain millions of records. Auditors are expected to test entire populations rather than small samples. Management accountants are asked to explain variances, forecast performance, and identify operational drivers using data that lives in systems they were never trained to access. Financial reporting teams must reconcile, validate, and analyze data that flows from dozens of interconnected tables before it reaches the financial statements. The profession needs practitioners who can work directly with data, and accounting education needs textbooks that teach them how.

This textbook teaches accounting students to extract, prepare, analyze, and visualize data using three tools that are widely used in professional practice. Microsoft Excel serves as the foundation for data preparation, descriptive analytics, statistical modeling, and audit testing. SQL provides the ability to query relational databases directly, joining tables, aggregating results, and performing population-level analysis without relying on pre-built reports. Microsoft Power BI enables the creation of interactive dashboards and reports that communicate analytical findings to diverse audiences. These three tools cover the full analytics workflow from data access through communication of results, and they represent the toolkit that employers consistently identify as most relevant for entry-level accounting professionals (Sledgianowski, Gomaa, and Tan, 2017).

The book is built around one integrated dataset that students use throughout all twenty chapters. The Charles River Accounting Dataset follows a single fictional mid-size home furnishings company through its complete business cycles, and the same data underlies every chapter regardless of which tool that chapter teaches. The About the Dataset section that follows this preface describes the company, the ten table groups, the business cycles, and the distribution formats in full detail.


## Why This Book

Several features distinguish this textbook from other analytics resources available to accounting instructors.

The first is its focus on accounting. General-purpose data analytics textbooks teach techniques using data from marketing, healthcare, sports, or other domains. Those examples are interesting but do not help accounting students see how analytics connects to the work they will actually do. Every example, exercise, and case in this book uses accounting data and addresses accounting questions. Students analyze revenue trends, prepare trial balances, test for duplicate payments, calculate cost variances, perform Benford's Law analysis, and build financial reporting dashboards. The analytical techniques are the same ones taught in general analytics courses, but the context is always accounting, which helps students transfer what they learn to professional practice.

The second is its three-perspective exercise structure. Every chapter includes applied exercises organized into three sections by accounting perspective. Financial Accounting exercises address reporting, disclosure, and compliance questions. Managerial Accounting exercises address costing, budgeting, performance measurement, and decision support questions. Auditing exercises address assurance, control testing, anomaly detection, and risk assessment questions. This structure ensures that students see how the same analytical technique serves different purposes depending on the professional role. An aging analysis, for example, appears as a financial reporting exercise (estimating the allowance for doubtful accounts), a managerial accounting exercise (assessing collection efficiency), and an auditing exercise (evaluating management estimates and selecting balances for confirmation). Students who encounter all three perspectives develop a broader understanding of how analytics creates value across the profession.

The third is its integrated tool progression. Many textbooks teach Excel, SQL, and visualization tools in isolation. This book teaches them as complementary stages of a single workflow. Part II covers Excel. Part III covers SQL. Part IV covers Power BI. Part V brings all three tools together in integrated projects where students extract data using SQL, analyze it in Excel, and present results in Power BI within a single engagement. This progression mirrors how analytics projects work in practice, where no single tool handles every stage.

The fourth is its design as an open educational resource. The book and its companion dataset are freely available, and every tool used in the exercises is either free or included with standard institutional licenses. The Open Access section on the book's landing page describes the licensing terms in detail.


## Pedagogical Design

The book follows a consistent pedagogical structure that reflects research on how students learn technical skills most effectively. Worked examples, immediate practice opportunities, and progressive complexity have been shown to support skill acquisition in technology-intensive courses (Borthick and Jones, 2000). Every chapter in this book applies these principles through a structured sequence.

Each chapter opens with four to six learning objectives written in measurable terms using action verbs drawn from Bloom's taxonomy. The objectives span multiple cognitive levels, from foundational understanding through application and analysis, so that both undergraduate and graduate students find appropriate challenges. Following the objectives, an opening scenario places the student in a realistic professional situation at Charles River, the company whose data students use throughout the book. The scenario names a role, describes a concrete task, and motivates the material that follows by showing students why it matters before they learn how to do it.

The body of each chapter presents concepts in narrative paragraph form, supported by figures, tables, and diagrams. One to three guided tutorials are embedded within the conceptual content at the point where the relevant technique is introduced, so students read about a concept and immediately practice it before moving to the next topic. Each tutorial includes numbered steps, expected outputs, and a checkpoint that allows students to verify their work. Three types of callout boxes appear throughout the narrative. "In Practice" notes describe how the technique is used in professional settings. "Watch Out" notes warn about common errors and pitfalls. "Connecting the Dots" notes link the current topic to material in other chapters or other tools, helping students see the book as an integrated whole.

Each chapter closes with a summary, a list of key terms with definitions, ten to fifteen multiple choice questions spanning recall, application, and judgment, and applied exercises organized by the three accounting perspectives. Five comprehensive cases, one at the end of each of the book's five parts, provide extended multi-tool investigations that integrate material from all chapters in the part.

In-text citations in APA format appear throughout the narrative to support claims about professional practice, technique effectiveness, and adoption trends. Each chapter closes with a Further Reading section containing five to eight annotated references drawn from peer-reviewed journals, professional standards, and practitioner publications.


## Audience and Course Design

This textbook serves both undergraduate and graduate four-credit courses in accounting analytics or accounting information systems. A single text serves both audiences. The instructor controls the depth and rigor of classroom discussions and analyses to match the course level. Undergraduate courses can focus on the guided tutorials and foundational exercises. Graduate courses can emphasize the analytical judgment required by the applied exercises and comprehensive cases, assign additional readings from the Further Reading sections, and incorporate extended discussion of professional standards and research findings.

The book assumes no prior analytics or programming experience. Students need only the accounting knowledge gained from introductory financial and managerial accounting courses. Every technical concept is introduced from the ground up, and every tool is taught through step-by-step instruction before students are asked to work independently. Students who have prior experience with Excel, SQL, or Power BI will move through the early chapters faster and can focus their effort on the accounting applications and the more advanced techniques in later chapters.


## Suggested Course Schedules

The following schedules are suggestions, not prescriptions. Instructors should adapt them to their program's requirements, their students' preparation, and their own areas of emphasis.

For an undergraduate course spanning fifteen weeks, Week 1 covers Chapters 1 and 2, introducing analytics and understanding data through the Charles River order-to-cash tables. Week 2 covers Chapter 3, the accounting data environment, where students explore the full Charles River schema. Weeks 3 through 4 cover Chapters 4 and 5, Excel essentials and data preparation. Weeks 5 through 6 cover Chapters 6 and 7, descriptive analytics and modeling. Week 7 covers Chapter 8, Excel for audit analytics, introducing the Accounting Core and procure-to-pay tables. Weeks 8 through 9 cover Chapters 9 and 10, introduction to SQL and joining data. Week 10 covers Chapters 11 and 12, intermediate SQL and audit analytics. Week 11 covers Chapter 13, visualization principles. Weeks 12 through 13 cover Chapters 14 and 15, Power BI fundamentals and data modeling. Week 14 covers Chapter 16, building accounting dashboards. Week 15 covers selected topics from Chapters 17 through 20, along with the capstone project presentation.

For a graduate course spanning fifteen weeks, the pace is faster and the emphasis shifts toward analytical judgment and integration. Week 1 covers Chapters 1 through 3 as a combined foundational session. Week 2 covers Chapters 4 and 5 at an accelerated pace. Week 3 covers Chapters 6 and 7 with emphasis on modeling and analytical judgment. Week 4 covers Chapter 8 with deeper discussion of audit standards and professional skepticism. Weeks 5 through 6 cover Chapters 9 through 11 with emphasis on CTEs, window functions, and the full Charles River schema. Week 7 covers Chapter 12 with extended case analysis requiring multi-step SQL investigation. Week 8 covers Chapters 13 and 14. Week 9 covers Chapter 15 with advanced DAX and complex multi-group data models. Week 10 covers Chapter 16 with emphasis on dashboard design for different stakeholder audiences. Week 11 covers Chapter 17, financial reporting analytics. Week 12 covers Chapter 18, cost and management accounting analytics. Week 13 covers Chapter 19, forensic accounting and fraud analytics. Week 14 covers Chapter 20, emerging technologies, supplemented by assigned readings from the academic literature. Week 15 involves the capstone project presentation and discussion.


## How This Book Is Organized

The book contains twenty chapters organized into five parts that follow a deliberate progression. Part I (Chapters 1 through 3) builds the conceptual foundation without introducing any tools. Parts II, III, and IV each teach one tool in depth, with Excel covered in Chapters 4 through 8, SQL in Chapters 9 through 12, and Power BI in Chapters 13 through 16. Part V (Chapters 17 through 20) integrates all three tools in applied projects that span financial reporting, cost accounting, forensic analytics, and emerging technologies. A comprehensive case closes each part, requiring students to combine material from all chapters in that part into a multi-component deliverable.

Six appendices provide reference material including a software installation guide, complete dataset documentation with Entity-Relationship diagrams, and quick reference guides for Excel functions, SQL syntax, and DAX functions. Appendix F maps every exercise in the book to the relevant competency areas in the AICPA, IMA, and IFAC frameworks, supporting instructors who need to align their course with accreditation requirements.


## A Note on Professional Standards and Research

This textbook references professional standards and peer-reviewed research throughout its chapters. These references serve two purposes. First, they ground the analytical techniques in the professional context where students will apply them. When a chapter on audit analytics references the AICPA's guidance on data analytics in auditing (AICPA, 2017), students see that the techniques they are learning are not academic exercises but tools that professional standards expect them to use. Second, the references connect the practical instruction to the broader body of knowledge in accounting and information systems. Students who read the annotated Further Reading sections will find pathways into the research literature that informs and extends what the textbook teaches.

The profession's integration of analytics into its competency frameworks has accelerated in recent years. The AICPA has embedded data analytics across its pre-certification curriculum. The IMA has emphasized technology and analytics in the Certified Management Accountant examination content. The IFAC has published guidance on the technology competencies that accounting graduates need (IFAC, 2019). These developments confirm that the skills taught in this book are not supplementary. They are foundational to the practice of accounting in the current environment.

## References

AICPA (American Institute of Certified Public Accountants). (2017). *Guide to audit data analytics.* AICPA.

Borthick, A. F., and Jones, D. R. (2000). The motivation for collaborative discovery learning online and its application in an information systems assurance course. *Issues in Accounting Education*, 15(2), 181-210.

IFAC (International Federation of Accountants). (2019). *Technology and the profession: A guide for professional accountancy organizations.* IFAC.

Sledgianowski, D., Gomaa, M., and Tan, C. (2017). Toward integration of Big Data, technology, and information systems competencies into the accounting curriculum. *Journal of Accounting Education*, 38, 81-93.
