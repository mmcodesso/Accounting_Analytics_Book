---
number-sections: false
format:
  html:
    number-sections: false
---

# To the Student {.unnumbered}

You are beginning a book that will change how you work with accounting data. The accounting courses you have taken so far taught you to understand financial statements, apply standards, calculate ratios, and interpret results. Those skills remain essential. What this book adds is the ability to work directly with the data that produces those statements, ratios, and results. Instead of receiving a finished trial balance and analyzing it, you will learn to query a database, extract the general ledger entries, and build the trial balance yourself. Instead of reading a variance report, you will learn to calculate the variances from production data and present them in an interactive dashboard. Instead of reviewing a sample of transactions that someone else selected, you will learn to test the entire population and let the data reveal the anomalies.

This book assumes no prior experience with analytics or programming. If you have never written a SQL query, never built a PivotTable, and never opened Power BI, you are exactly the audience this book was written for. Every technique is introduced from the ground up with step-by-step guided tutorials that you can follow at your own pace. The tutorials build on one another, so the output of one often serves as the input for the next, and the complexity increases gradually across chapters.


## What to Expect

The book follows a consistent structure that will become familiar after the first few chapters. Each chapter opens with learning objectives that tell you what you will be able to do after completing the chapter. An opening scenario places you in a professional role and describes a task that motivates the material. The body of the chapter alternates between conceptual explanation and hands-on tutorials. Callout boxes provide practical tips, warnings, and connections to other parts of the book. Each chapter closes with a summary, key terms, review questions, and applied exercises.

The applied exercises at the end of each chapter sit in three sections by accounting perspective, namely financial accounting, managerial accounting, and auditing. You will complete exercises in all three perspectives regardless of which area of accounting interests you most, because analytical techniques transfer across roles and understanding how the same technique serves different purposes will broaden your professional range.


## The Three Tools

You will learn three tools in this book, each suited to a different stage of the analytics workflow.

Microsoft Excel is the tool you will use first. Chapters 4 through 8 teach you to organize data in structured tables, clean and prepare messy data, build PivotTables for summarization, run regression models, and perform audit analytics procedures. Excel is most powerful for ad hoc analysis, financial modeling, and workpaper preparation.

SQL is introduced in Chapters 9 through 12. SQL stands for Structured Query Language, and it is the standard language for retrieving data from relational databases. You will use a free, lightweight database system called SQLite that requires no server and runs on any operating system. SQL is most powerful when working with large datasets, when data spans multiple related tables that must be combined, and when you want to save and reuse your analytical procedures.

Microsoft Power BI is introduced in Chapters 13 through 16. Power BI is a business intelligence platform that lets you build interactive dashboards and reports. You will connect Power BI to the same Charles River data you used in Excel and SQL, create data models, write DAX formulas for calculated measures, and design dashboards that stakeholders can explore on their own.

In Part V of the book, you will use all three tools together. You will extract data with SQL, analyze it in Excel, and present results in Power BI within a single integrated project.


## The Dataset

You will work with one dataset throughout this book, the Charles River Accounting Dataset. Charles River is a fictional mid-size home furnishings company that sells goods, manufactures selected product lines, and provides hourly design services, generating the full range of accounting transactions you will analyze across the chapters. The dataset ships as an SQLite database, an Excel workbook, and a CSV package, so you can use the same data in every tool the book covers. The About the Dataset section that follows describes the company, the table groups, and the formats in full detail.


## How to Succeed

The most important habit you can develop is to do the tutorials yourself rather than reading through them passively. Open the dataset, follow the steps, and verify your results at each checkpoint. When you make an error, diagnosing and correcting it teaches you more than getting it right the first time. The guided tutorials are designed so that you can complete them independently at your own pace, and they prepare you directly for the applied exercises that follow.

A second important habit is to read the conceptual material before jumping to the tutorials. The concepts explain why a technique works and when it is appropriate. The tutorials show you how to execute it. Both are necessary. A student who can execute a Benford's Law analysis without understanding what the results mean or when the test is appropriate has a technical skill but not an analytical one. This book aims to develop both.

Finally, pay attention to the connections across chapters and tools. The "Connecting the Dots" callout boxes link the current topic to material elsewhere in the book. The three-perspective exercise structure shows you how the same technique applies in different contexts. The comprehensive cases at the end of each part ask you to integrate everything you have learned. These connections are where the deepest learning happens, because they move you from knowing how to use a tool to understanding how to solve a problem.