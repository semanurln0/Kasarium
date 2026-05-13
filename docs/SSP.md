# Semester Project — Smart Student Portal (SSP)

Proposed Project Title: Smart Student Portal (SSP)

Type: Semester-long practical project (built gradually during laboratories)

Project Mode: Individual

Project Flexibility

The project brief below is provided as a recommended guide and reference implementation to help students understand the expected scope, technologies, and learning outcomes of the laboratory work. Students are allowed to choose their own project idea or develop an alternative solution, if it demonstrates the same required concepts and satisfies the course laboratory requirements (HTML/CSS, JavaScript, XML/XSLT, backend framework usage, database integration, flow management with templates, validation, and session management). Students who choose a different project must ensure their proposed system is approved by the lecturer and includes all mandatory features listed in this document.

1. Project Description

In this project, students will design and implement a complete web application called Smart Student Portal (SSP). The goal is to demonstrate practical understanding of modern internet technologies and website development by progressively building one coherent system across the semester.

The project integrates the following core areas:

- Website structure and styling (HTML, CSS)
- Client-side programming (JavaScript)
- Structured data and transformations (XML + XSLT)
- Backend framework deployment and usage
- Database integration and data management
- Flow management and template-based output rendering
- Data validation and session management mechanisms

2. Project Scenario

A university department requires a web portal to manage student records. The portal should allow an administrator to store, view, and update student information in a structured and user-friendly way.

3. Learning Outcomes

By completing this project, students will be able to:

- Build a structured website using HTML5 and CSS3
- Implement interactive behaviour using JavaScript
- Use XML and XSLT to represent and transform data into HTML
- Deploy and use a backend framework for dynamic web applications
- Connect a web application to a database and perform data operations
- Implement proper routing and flow between pages using templates
- Apply validation rules and session-based access control

4. Functional Requirements (Mandatory Features)

FR1: Public Website Pages

The system must include at least the following pages:

- Home Page: description of the portal and its purpose
- About Page: information about the system features
- Contact Page: a contact form (UI only is acceptable unless backend handling is required)

FR2: Student Management Module (CRUD)

The system must support full student record management:

Required functions:

- List Students (table view)
- View Student Details (single record page)
- Add New Student (form + database insert)
- Edit Student Information (update database)
- Delete Student Record (remove from database)

Minimum student fields:

Each student record must include at least:

- Student ID (unique)
- Full Name
- Email
- Program/Department
- Year of Study
- Status (Active / Inactive)

FR3: Data Validation

Validation must be implemented at two levels:

A) Client-side validation (JavaScript)

- Required fields must not be empty
- Email format must be checked
- Student ID must follow a valid pattern
B) Server-side validation (Backend)

- Input must be validated again before saving to the database
- Duplicate Student ID must be rejected
- Invalid input must show a clear error message

FR4: Flow Management + Output Templates

The application must implement clear routing and navigation between pages.

Minimum required flow:

- /home
- /students (student list)
- /students/new (create student)
- /students/:id (student details)
- /students/:id/edit (edit student)
Templates/views must be used to generate output pages (not hard-coded HTML responses).

FR5: Session Management

The system must demonstrate session-based behavior such as:

- Login page (simple admin login)
- Restricted access to student management pages unless logged in
- Logout function
- Session feedback messages (example: “Student added successfully”)

FR6: XML + XSLT Requirement

The project must include at least one XML/XSLT feature:

Example requirement:

- Export student data into an XML file
- Use XSLT to transform the XML into an HTML report
- Display the report in the browser (e.g., “Student Report” page)

5. Non-Functional Requirements (Quality Requirements)

The project should demonstrate:

- Clean and organized folder structure
- Readable code and consistent naming
- User-friendly navigation and layout
- Proper error handling (e.g., invalid student ID, missing record)
- Basic secure coding practices (do not trust user input)

6. Technologies and Tools

Students must use the following technologies:

- HTML5
- CSS3
- JavaScript
- XML + XSLT
- A backend framework (approved by the lecturer)
- A database system (relational database recommended)

7. Deliverables and Submission Requirements

Students must submit the following:

(a) Complete Source Code

Full project folder with all files
(b) Database Setup

One of the following:

.sql script to create tables and sample records
OR
clear written instructions for database setup
(c) README File

Must include:

- Project description
- Instructions on how to run the project
- Required dependencies/tools
- Login credentials for testing
- List of implemented features
(d) Screenshots

Provide screenshots of:

- Student list page
- Add/Edit student form page
- XML/XSLT report page
- Login/logout and restricted access behaviour

8. Laboratory Alignment (Project Development Plan)

This project will be built gradually in laboratory sessions and will cover:

- HTML/CSS website structure and design
- JavaScript DOM manipulation and validation
- XML and XSLT transformation tasks
- Backend routing and template rendering
- Database integration and CRUD implementation
- Flow management between system pages
- Validation and session mechanisms

9. Optional Extensions (Bonus Features)

Students may implement additional features such as:

- Search and filtering students
- Pagination of student list
- AJAX-based search without reloading the page
- Role-based access control (Admin / Viewer)
- Export student data to JSON
- Improved UI design and responsiveness
