# University-Industry Collaboration (UIC) Platform

## 📋 Project Overview

The UIC Platform is a comprehensive Django-based web application designed to bridge the gap between universities, students, and companies by facilitating project-based collaborations. The platform enables companies to post projects, students to apply and work on them, and universities to oversee and verify all interactions.

### Core Concept
- **Companies** post projects requiring student talent
- **Students** browse, apply, and complete projects to gain experience and earn remuneration
- **Universities** act as intermediaries, verifying both companies and students while approving projects

---

##  Key Features

### Multi-User Authentication System
- **Three User Types**: Students, Companies, and Universities
- **Role-based Access Control**: Each user type has distinct permissions and dashboards
- **Verification Workflow**: Universities verify both students and companies before they can fully participate

### For Students
-  Browse and search available projects by domain, university, and payment range
-  Apply to projects with cover letters and proposed approaches
-  Track application status (pending, accepted, rejected, shortlisted)
-  Work on assigned projects with milestone tracking
-  Submit deliverables for company review
-  Build portfolio with completed projects
-  University verification required before accessing platform

### For Companies
-  Post projects with detailed requirements and job descriptions
-  Set eligibility criteria (departments, years, minimum GPA)
-  Choose between fixed payment or milestone-based payment
-  Review and manage student applications
-  Accept/reject applications and assign students
-  Create milestones for project tracking
-  Review and approve student deliverables
-  Provide feedback and request revisions
-  University verification required before posting projects

### For Universities
-  Verify student profiles (USN, university email validation)
-  Verify company profiles (registration number, documents)
   Review and approve company-posted projects
-  Post their own projects (auto-approved)
-  Manage applications to university-posted projects
-  Oversee all activities within their institution
-  Dashboard with comprehensive statistics

---

## 🏗️ Technical Architecture

### Technology Stack
- **Backend**: Django 4.x (Python web framework)
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **Frontend**: Bootstrap 5.3.2 with custom styling
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Icons**: Bootstrap Icons
- **Authentication**: Django's built-in authentication system

### Project Structure
```
uic_platform/
├── apps/
│   ├── accounts/          # User management & authentication
│   │   ├── models.py      # User, Student, Company, University models
│   │   ├── views.py       # Registration, profile, dashboards
│   │   ├── forms.py       # Registration and profile forms
│   │   └── urls.py        # Account-related routes
│   │
│   ├── projects/          # Project management
│   │   ├── models.py      # Project, Application, Milestone, Deliverable
│   │   ├── views.py       # CRUD operations, applications, workspace
│   │   ├── forms.py       # Project creation and milestone forms
│   │   └── urls.py        # Project-related routes
│   │
│   ├── messaging/         #  Not yet implemented
│   ├── payments/          #  Not yet implemented
│   └── reviews/           #  Not yet implemented
│
├── config/                # Django project configuration
│   ├── settings.py        # Main settings
│   ├── urls.py           # Root URL configuration
│   └── wsgi.py           # WSGI configuration
│
├── templates/
│   ├── base.html         # Base template with navbar
│   ├── home.html         # Landing page
│   ├── accounts/         # Authentication & profile templates
│   ├── dashboard/        # User-specific dashboards
│   └── projects/         # Project-related templates
│
├── static/               # Static files (CSS, JS, images)
├── media/                # User uploads (logos, resumes, documents)
└── manage.py             # Django management script
```

---

## Database Models

### User Model (Custom)
```python
class User(AbstractUser):
    user_type: student | company | university
    email_verified: Boolean
    phone: String
```

### Student Model
```python
class Student:
    user: OneToOne → User
    university: ForeignKey → University (nullable until verification)
    student_id: String (USN)
    university_email: Email (for verification)
    department: String
    year: Choice (1-4, graduate)
    gpa: Decimal (0-10)
    skills: Text (comma-separated)
    is_verified: Boolean
    verification_status: pending | approved | rejected
```

### Company Model
```python
class Company:
    user: OneToOne → User
    name: String
    logo: ImageField
    industry: String
    contact_person: String (SPOC)
    contact_email: Email (official)
    company_registration_number: String (CIN)
    gst_number: String (optional)
    verification_document: FileField
    is_verified: Boolean
    verification_status: pending | approved | rejected
    verified_by: ForeignKey → University
```

### University Model
```python
class University:
    user: OneToOne → User
    name: String
    logo: ImageField
    admin_name: String
    admin_email: Email
    is_verified: Boolean (auto-verified on registration)
    auto_approve_projects: Boolean
    min_payment_amount: Decimal
```

### Project Model
```python
class Project:
    poster_type: company | university
    company: ForeignKey → Company (nullable)
    university: ForeignKey → University
    posted_by_university: Boolean
    
    title: String
    domain: Choice (design, coding, marketing, etc.)
    description: Text
    required_skills: Text
    job_type: remote | hybrid | onsite
    
    team_type: individual | team
    team_size: Integer
    eligible_departments: Text (comma-separated)
    eligible_years: Text
    min_gpa: Decimal
    
    payment_amount: Decimal (renamed from "payment" to "remuneration")
    payment_type: fixed | milestone
    duration_weeks: Integer
    deadline: Date (renamed to "Project Closure Date")
    attachment: FileField (Job Description/JD)
    
    status: draft | pending_review | rejected | open | in_progress | completed | cancelled
    assigned_students: ManyToMany → Student
```

### ProjectApplication Model
```python
class ProjectApplication:
    project: ForeignKey → Project
    student: ForeignKey → Student
    cover_letter: Text
    proposed_approach: Text
    portfolio_links: Text
    is_team_application: Boolean
    team_members: ManyToMany → Student
    status: pending | shortlisted | accepted | rejected | withdrawn
```

### Milestone Model
```python
class Milestone:
    project: ForeignKey → Project
    title: String
    description: Text
    order: Integer
    payment_percentage: Decimal (0-100)
    due_date: Date
    status: pending | in_progress | submitted | approved | revision_required
```

### Deliverable Model
```python
class Deliverable:
    project: ForeignKey → Project
    student: ForeignKey → Student
    milestone: ForeignKey → Milestone (optional)
    title: String
    description: Text
    file: FileField
    is_approved: Boolean
    feedback: Text
    revision_required: Boolean
```

---

## 🔐 Access Control & Permissions

### Student Access
- ✅ Can view only projects from their own university
- ✅ Must be verified by university before accessing projects
- ✅ Can apply to open projects matching their eligibility
- ✅ Can submit deliverables only for assigned projects
- ❌ Cannot post projects
- ❌ Cannot see projects from other universities

### Company Access
- ✅ Must be verified by a university before posting projects
- ✅ Can post projects to any verified university
- ✅ Can manage applications to their own projects
- ✅ Can review and approve deliverables
- ✅ Can create milestones for their projects
- ❌ Cannot see other companies' projects or applications
- ❌ Cannot directly message students (messaging not yet implemented)

### University Access
- ✅ Auto-verified upon registration
- ✅ Can verify students from their institution
- ✅ Can verify companies requesting to post projects
- ✅ Can review and approve company-posted projects
- ✅ Can post their own projects (auto-approved, skips review)
- ✅ Can manage applications to university-posted projects
- ✅ Can view all activities within their institution
- ❌ Cannot see other universities' data

---

##  Core Workflows

### 1. Student Registration & Verification Flow
```
1. Student registers (username, email, password)
2. Student completes profile:
   - Selects university from dropdown
   - Provides USN/Student ID
   - Provides official university email
   - Adds academic details (department, year, GPA)
3. Profile submitted to university for verification
4. University admin reviews:
   - Checks USN validity
   - Verifies university email domain
   - Validates academic information
5. University approves/rejects
6. If approved: Student can access projects
   If rejected: Student must update profile and resubmit
```

### 2. Company Registration & Verification Flow
```
1. Company registers (username, email, password)
2. Company completes profile:
   - Company name and details
   - SPOC (Single Point of Contact) information
   - Official company email
   - Company Registration Number / CIN
   - GST Number (optional)
   - Upload verification documents (incorporation certificate, etc.)
3. Profile submitted for university verification
4. University admin reviews:
   - Validates company registration number
   - Checks official email domain
   - Reviews uploaded documents
5. University approves/rejects
6. If approved: Company can post projects
   If rejected: Company must update and resubmit
```

### 3. Company Posts Project Flow
```
1. Verified company clicks "Post New Project"
2. Fills project form:
   - Basic info (title, domain, description)
   - Requirements (skills, team type, job type)
   - Eligibility (departments, years, min GPA)
   - Remuneration (amount, type: fixed/milestone)
   - Timeline (duration, closure date)
   - Upload JD (Job Description) document
3. Selects target university
4. Project submitted with status "pending_review"
5. University admin reviews project
6. University approves/rejects
7. If approved: Project becomes "open" for applications
   If rejected: Company can edit and resubmit
```

### 4. University Posts Project Flow
```
1. University admin clicks "Post Project"
2. Fills project form (same as company)
3. Project is auto-approved (status: "open")
4. Immediately visible to students
5. University manages applications directly
```

### 5. Student Application Flow
```
1. Student browses projects (filtered by their university)
2. Clicks "Apply Now" on a project
3. Fills application form:
   - Cover letter
   - Proposed approach
   - Portfolio links
   - Team application (optional)
4. Application submitted with status "pending"
5. Company/University reviews application
6. Can shortlist, accept, or reject
7. If accepted:
   - Student added to assigned_students
   - Project status changes to "in_progress"
   - Student can access project workspace
```

### 6. Milestone-Based Project Flow
```
1. Company/University creates milestones after accepting student
2. Each milestone has:
   - Title, description
   - Payment percentage (must total 100%)
   - Due date
3. Student submits deliverable for milestone
4. Company reviews:
   - Approve → Milestone marked complete
   - Request revision → Student resubmits
5. When all milestones approved → Project completed
```

---

##  User Interface Components

### Dashboards

#### Student Dashboard
- **Stats Cards**: Active projects, completed projects, pending applications
- **Active Projects**: List of assigned projects with status
- **Recent Applications**: Table showing application status
- **Profile Preview**: Quick stats (rating, completed projects)
- **Quick Actions**: Browse projects, view applications, edit profile

#### Company Dashboard
- **Stats Cards**: Active projects, pending review, total projects, rating
- **Clickable Stats**: Click to filter projects by status
- **Recent Projects**: List with application counts and status badges
- **Quick Actions**: Post project, view all projects, view pending reviews
- **Project Management**: Direct links to manage applications

#### University Dashboard
- **Stats Cards**: Pending reviews, active projects, pending students, total students, verified companies
- **Pending Reviews**: Company-posted projects awaiting approval
- **Pending Students**: Students awaiting verification (clickable card)
- **Active Projects**: Mix of company and university projects
- **Quick Actions**:
  - Post new project
  - Manage students (with pending count badge)
  - Manage companies (with pending count badge)
  - Manage applications (for university projects)
  - Review company projects
  - View all projects

### Project Views

#### Project List Page
- **Filters**: Search, domain, university, payment range
- **Project Cards**: Display title, company/university, payment, skills, domain
- **Visual Indicators**: 
  - Verified badges for companies
  - "University Project" badge for uni-posted projects
  - Status badges

#### Project Detail Page
- **Left Column**: Detailed project information
  - Description, required skills
  - Team type, duration, deadline
  - Eligibility criteria
  - Job type (Remote/Hybrid/On-site)
  - Download JD button
- **Right Column**: 
  - Company/University profile card
  - Quick stats
  - Contact information
  - Verification status

#### Application Management
- **For Companies/Universities**:
  - List all applications with student profiles
  - Student cards showing:
    - Avatar, name, academic info
    - GPA with color-coded badges
    - Skills preview
    - Cover letter
    - Proposed approach (collapsible)
    - Portfolio links
  - Action buttons:
    - View full profile
    - Shortlist (for universities)
    - Accept
    - Reject

#### Project Workspace
- **Milestone View**: List of all milestones with status
- **Progress Bar**: Visual representation of project completion
- **Deliverables**: Grouped by milestone
- **For Students**: Submit deliverable button
- **For Companies**: Review and approve deliverables

---

## 🔧 Configuration & Setup




## 📁 File Upload Handling

### Supported File Types
- **Profile Pictures**: JPG, PNG (max 5MB)
- **Resumes**: PDF, DOC, DOCX (max 10MB)
- **Company Documents**: PDF (max 10MB)
- **Project Attachments (JD)**: PDF, DOC, DOCX (max 10MB)
- **Deliverable Files**: All common formats (max 10MB)

### Upload Paths
```
media/
├── students/           # Student profile pictures
├── resumes/           # Student resumes
├── companies/         # Company logos
├── company_docs/      # Company verification documents
├── universities/      # University logos
├── project_attachments/  # Job Description files
└── deliverables/      # Student submission files
```

---

##  Pending Features (Not Yet Implemented)

### 1. Messaging System (`apps/messaging/`)
**Planned Features**:
- Real-time chat between companies and students
- Project-specific message threads
- University can monitor conversations
- File sharing in messages
- Notification system for new messages

**Suggested Models**:
```python
class Conversation:
    participants: ManyToMany → User
    project: ForeignKey → Project
    created_at: DateTime

class Message:
    conversation: ForeignKey → Conversation
    sender: ForeignKey → User
    content: Text
    attachment: FileField (optional)
    timestamp: DateTime
    is_read: Boolean
```

### 2. Payments System (`apps/payments/`)
**Planned Features**:
- Integration with payment gateways (Stripe/Razorpay)
- Escrow system for milestone-based payments
- Automatic release on deliverable approval
- Payment history and invoicing
- Transaction tracking
- Bank account verification for students

**Suggested Models**:
```python
class Payment:
    project: ForeignKey → Project
    payer: ForeignKey → Company
    payee: ForeignKey → Student
    amount: Decimal
    payment_type: milestone | fixed
    milestone: ForeignKey → Milestone (if milestone-based)
    status: pending | completed | failed | refunded
    transaction_id: String
    paid_at: DateTime

class BankAccount:
    student: ForeignKey → Student
    account_holder_name: String
    account_number: String
    ifsc_code: String
    bank_name: String
    is_verified: Boolean
```

### 3. Reviews & Ratings System (`apps/reviews/`)
**Planned Features**:
- Companies can rate students after project completion
- Students can rate companies and projects
- Review comments and feedback
- Rating aggregation (displayed on profiles)
- Review moderation by universities

**Suggested Models**:
```python
class Review:
    reviewer: ForeignKey → User
    reviewee: ForeignKey → User (Student or Company)
    project: ForeignKey → Project
    rating: Integer (1-5)
    comment: Text
    created_at: DateTime
    is_approved: Boolean (university moderation)

class Response:
    review: ForeignKey → Review
    responder: ForeignKey → User
    content: Text
    created_at: DateTime
```

---

##  Key Design Decisions

### 1. University as Central Authority
- Universities act as gatekeepers for both students and companies
- All projects must be submitted to a specific university
- Students can only see projects from their own university
- Ensures quality control and institutional oversight

### 2. Dual Project Posting
- Companies can post projects (requires university approval)
- Universities can post their own projects (auto-approved)
- Allows universities to create internal opportunities

### 3. Verification Workflow
- **Students**: Must provide USN and university email
- **Companies**: Must provide registration number and documents
- Reduces fraud and ensures legitimacy

### 4. Flexible Payment Options
- **Fixed Payment**: Single payment upon project completion
- **Milestone-Based**: Split payments across defined milestones
- Accommodates different project types and complexities

### 5. Eligibility Filtering
- Projects can specify eligible departments and years
- Minimum GPA requirements
- Ensures right-fit applications

### 6. Terminology Changes
- "Payment" → "Remuneration" (more professional)
- "Deadline" → "Project Closure Date" (clearer meaning)
- Emphasizes work quality over transactional nature

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. **No Real-time Communication**: Messaging system not implemented
2. **Manual Payment Tracking**: No automated payment processing
3. **No Notification System**: Users must check manually for updates
4. **Basic Search**: No advanced filtering or recommendation engine
5. **No Analytics Dashboard**: Limited insights for universities
6. **Single University per Student**: Cannot transfer between universities
7. **No Project Templates**: Companies must create from scratch each time
8. **Limited File Format Validation**: Based on extensions only

### Security Considerations
1. **File Upload Validation**: Currently basic, needs enhancement
2. **XSS Protection**: Django's built-in protection active
3. **CSRF Protection**: Enabled on all forms
4. **SQL Injection**: Protected by Django ORM
5. **Password Storage**: Django's PBKDF2 algorithm
6. **HTTPS**: Should be enforced in production

---

## 📈 Future Enhancement Ideas

### Short-term 
- [ ] Email notifications for application status changes
- [ ] Password reset functionality
- [ ] Project search history for students
- [ ] Export project reports for universities
- [ ] Bulk student import via CSV for universities

### Medium-term
- [ ] Implement messaging system
- [ ] Payment gateway integration
- [ ] Reviews and ratings system
- [ ] Mobile-responsive dashboard improvements
- [ ] Project templates for quick posting
- [ ] Advanced analytics for universities

### Long-term
- [ ] AI-powered student-project matching
- [ ] Skill assessment tests
- [ ] Virtual interview scheduling
- [ ] Portfolio builder for students
- [ ] Company reputation scoring
- [ ] Multi-university consortium support
- [ ] API for third-party integrations

---

## 📝 Version History

### v1.0.0 (Current)
- ✅ Multi-user authentication (Student, Company, University)
- ✅ Verification workflows for students and companies
- ✅ Project CRUD operations
- ✅ Application management system
- ✅ Milestone and deliverable tracking
- ✅ Role-based access control
- ✅ Responsive UI with Bootstrap 5
- ❌ Messaging system (pending)
- ❌ Payment integration (pending)
- ❌ Reviews system (pending)

---

**Last Updated**: January 2026  
**Django Version**: 4.x  
**Python Version**: 3.8+  
**Status**: MVP Complete (Messaging, Payments, Reviews pending)
