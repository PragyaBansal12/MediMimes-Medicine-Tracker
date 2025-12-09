## 🏥 Project Overview

Many patients, especially those with chronic conditions, struggle with medication adherence. Forgetting doses or confusing schedules can lead to serious health risks. Existing solutions often lack personalization, proactive reminders, and intuitive user interfaces.

**MediMimes** fills this gap by combining:

- A user‑friendly medication scheduler   
- An interactive rag-based health chatbot assistant  

It not only reminds users to take medicines, but also conversational support. //improve this line

---
## Team Members

- **Pragya Bansal (20243208)** — https://github.com/PragyaBansal12 
- **Aadya (20243001)** — https://github.com/aadya75  
- **Naina (20243172)** — https://github.com/nainaamodii

---

## Tech Stack

- **Backend / Web Framework**: Django  
- **Authentication**: django-allauth, Google-auth 
- **Database**: SQLite3 (via Django ORM)  
- **Scheduling / Reminders**: APScheduler , Django backgroud tasks 
- **Browser Push Notifications**: pywebpush  
- **Google Calendar / OAuth**: google-api-python-client, google-auth, google-auth-oauthlib  
- **Data Processing / ML**: pandas, numpy, scikit-learn  
- **Chatbot**: langchain, langgraph  
- **Visualization**: Plotly  
- **Frontend / UI**: Bootstrap 
---
## Features

###  Robust Authentication System
- User registration and login  
- Secure session handling with Django authentication  
- Password hashing and admin management via Django Admin
- Multi-role login - patient, doctor and admin

### Patient Side Features 
- Personalized patient dashboard showing medication logs, upcoming appointments, and health activity
- Medication Management: Add daily medications, track intake history, receive reminders
- Appointment booking: View available doctors, book appointments
- Integrated Chatbot: Ai-powered smptom assistnace using LangGraph, Medicatoin informatoin via RAG (PDF knowledge base), safe, non-prescriptive general health guidance
- Notification system: Email alerts for medication schedules, appointment reminders, system-wide updates
- Profile and health data management

### Doctor Side Features
- Dedicated doctor dashboard
- View patient appointments
- Mark appointments as complete
- Update availability and time slots
- Access patient medication entries
- Approve or review patient reports
- Receive automatic notifications for new bookings

### Admin Portal Features
- Full access to system analytics
- Manage patients and dcotrs accounts
- View system-wide activity dashboard

### Appointment Management System
- Book appointments with available doctors
- Accept or cancel request on doctor side

### Notification service
- Medication alerts on web browser

### AI Chatbot (LangGraph + RAG)
- Intent classifier to route medical queries
- Safety nodes: Red Flag and Emergency Detector
- Symptom analysis (non-diagnostic)
- Medication information from structured PDF datasets
- Fallback and repair nodes for unclear queries
- Fast retrieval using Chroma vector search
- Strict safety compliance (non-prescriptive, no dosing advice)

### Google Calendar Integration
- OAuth-based secure calendar linking
- Auto-create events for docot appointments
- Sync reminders across devices

---

###  RAG Based Chatbot
- Built using LangGraph with a structured, multi-node conversational workflow.
- Includes a deterministic safety layer with Red Flag and Emergency nodes to detect critical symptoms.
- Uses an Intent Classifier to route queries to the correct medical-information node.
- Handles symptom queries via a non-prescriptive Symptom Node that provides safe, general guidance.
- Provides medication information through a RAG-powered Medication Node using PDF documents, embeddings, and Chroma vector search.
- Supports adherence and general medication understanding via an Adherence Node.
- Includes a Fallback Node for unclear queries to maintain reliability and reduce hallucinations.
- Maintains stateful, controlled conversation flow across all nodes for consistency and safety.

---

###  Live Chat Interface
- Smooth real-time chatbot UI  
- Typing indicators with streaming responses  
- Mobile-responsive design  

---
###  Data Management
- User profile section  
- Query history logs (optional)  
- Admin controls for uploading medical PDFs  
- SQLite-backed persistent storage  

---

###  Knowledge Blog (Optional Module)
- Public health-awareness article hub  
- Markdown-based editor  
- Django-admin moderation  

---
###  Session Management
- Django session-based login  
- Auto-logout after session expiry  

---

##  Process Flow

1. **User Authentication**  
   - User signs up / logs in  
2. **Medication Schedule Setup**  
   - Input pill name, dosage, time, frequency  
   - Stored in backend, synced with Google Calendar  
3. **Dashboard View**  
   - Shows upcoming doses, adherence history, medication schedule
4. **Reminder Notifications**  
   - At scheduled times, sends notification 
   - Buttons: “Taken” / “Missed”  
5. **Logging Dose Status**  
   - **Taken**:
     - Record status in DB  
     - Update calendar event  
     - Refresh dashboard graphs  
   - **Missed**:
     - Record status  
     - Update calendar event  
     - AI model analyzes for pattern  
     - Trigger proactive reminders if risk detected  
6. **AI Modules**    
   - **Chatbot Assistant**: natural language safe queries (personal data / medication related / general education / symptom logging / adherence tracking)  
7. **Visualization Dashboard**  
   - Graphs: adherence rates, missed doses, long‑term trends  
   - Insights into user behavior  
8. **Google Calendar Integration**  
   - Create events for doses  
   - Auto‑update if doses missed/rescheduled  

---
### Database Schema
<img width="1114" height="3107" alt="diagram-export-12-9-2025-3_10_20-PM" src="https://github.com/user-attachments/assets/0e3909f2-7a61-46be-b246-a529926fe6ce" />


---

```mermaid
sequenceDiagram
    autonumber

    participant U as User
    participant WB as Web Browser
    participant DJ as Django App
    participant AUTH as Auth Service
    participant MED as Medication Service
    participant DASH as Dashboard Service
    participant API as API Service
    participant NOTI as Notification Service
    participant GC as Google Calendar
    participant DOC as Doctor Portal
    participant BOT as Chatbot
    participant ADM as Admin Portal

    %% --- LOGIN FLOW ---
    U ->> WB: Navigate to login page
    WB ->> DJ: GET /login
    DJ ->> AUTH: Validate credentials
    AUTH -->> DJ: Success / Failure
    DJ -->> WB: Render home/dashboard

    %% --- USER DASHBOARD LOAD ---
    WB ->> DJ: GET /dashboard
    DJ ->> DASH: Fetch dashboard data
    DASH -->> DJ: Return stats
    DJ -->> WB: Render dashboard

    %% --- MEDICATION SUBMISSION ---
    U ->> WB: Submit medication form
    WB ->> DJ: POST /medication
    DJ ->> MED: Validate + Save medication
    MED -->> DJ: Success / Validation errors
    DJ -->> WB: Render response

    %% --- GOOGLE CALENDAR AUTH ---
    U ->> WB: Click "Connect Google Calendar"
    WB ->> DJ: GET /google-auth
    DJ ->> GC: OAuth request
    GC -->> DJ: Return auth token
    DJ -->> WB: Calendar connected

    %% --- BOOKING APPOINTMENT ---
    U ->> WB: Book appointment
    WB ->> DJ: POST /appointment
    DJ ->> DOC: Create appointment
    DOC -->> DJ: Confirmation
    DJ ->> GC: Add event
    GC -->> DJ: Event created
    DJ -->> WB: Show confirmation

    %% --- NOTIFICATION SYSTEM ---
    DJ ->> NOTI: Trigger notification
    NOTI -->> U: Email / Push notification sent

    %% --- CHATBOT INTERACTION ---
    U ->> WB: Ask health question
    WB ->> BOT: Send query
    BOT -->> WB: Response

    %% --- ADMIN PORTAL ---
    ADM ->> DJ: GET /admin
    DJ ->> API: Fetch admin metrics
    API -->> DJ: Return data
    DJ -->> ADM: Render admin dashboard

```

---

### Installation


---

### AI/ML Integration Details
```mermaid
flowchart TD

    U[User Input] --> IC[Intent Classifier]

    %% Safety Check
    IC --> EC{Emergency Detected?}
    EC -->|Yes| EM[Emergency Node]
    EM --> END

    %% Normal Flow
    EC -->|No| INT{Intent Type}

    INT -->|Symptom Query| SY[Symptom Node]
    INT -->|Medication Info| MD[Medication RAG Node]
    INT -->|Adherence Query| AD[Adherence Node]
    INT -->|General / Unknown| FB[Fallback Node]

    %% Medication RAG Flow
    MD --> R1[Create Embeddings]
    R1 --> R2[Chroma Vector Store]
    R2 --> R3[Retrieval QA]
    R3 --> ResponseGenerationNode

    %% Other Nodes End Here
    SY --> ResponseGenerationNode
    AD --> ResponseGenerationNode
    FB --> ResponseGenerationNode
    ResponseGenerationNode --> END

    END[END]

```
---
### Future Improvements

- adding session memory to chatbot
- multi-intent messages in chatbot 
- critical notifications choice for patient for nudge notifications 
-map based doctor recommendation system
-trend analysis for patient in dashboard (present in chatbot)
-payment gateway for appointment and premium feature access



