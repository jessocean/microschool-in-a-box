## **OUT App Specification for LLM-Powered IDE (e.g., Cursor)**

This document outlines the core functionality and user interface for "OUT," an app designed to simplify social coordination for parents. The focus is on a **simplest possible implementation** using a generic backend environment, with clear separation of concerns to facilitate development by an LLM-powered IDE.

---

### **1. Core Concepts & Data Models**

The application revolves around Users and Activities, stored in a key-value (KV) store or simple database.

#### **1.1. User Data Model**
    
Represents a single user within the system.

* `userId`: `UUID` (Unique identifier, assigned on registration)
* `name`: `String` (User's display name)
* `location`: `{lat: Number, lon: Number}` (Current geographic coordinates. For v1, this can be static or user-updated, not real-time GPS.)
* `transportModes`: `[String]` (e.g., "walk", "bike", "public_transport", "car")
* `socialCircles`: `{oldPals: [userId], friends: [userId], newFriends: [userId]}` (Lists of `userId`s categorized by intimacy level)
* `basicScheduleText`: `String` (Free-form text input for general availability, *not* computationally parsed in v1. Placeholder for future Google Calendar integration.)

#### **1.2. Activity Data Model**

Represents an event or availability broadcast by a user.

* `activityId`: `UUID` (Unique identifier for the activity)
* `ownerId`: `userId` (The user who created/broadcasted this activity)
* `type`: `String` ("open_door", "public_outing", "private_outing", "help_request")
* `title`: `String` (A brief, user-facing description)
* `description`: `String` (Optional, more detailed description)
* `location`: `{lat: Number, lon: Number}` or `String` (Geographic coordinates or a descriptive address)
* `startTime`: `DateTime` (ISO string, for scheduled activities. `null` for "open_door.")
* `endTime`: `DateTime` (ISO string, for scheduled activities. `null` for "open_door." Defaults to `startTime + 2 hours` if not specified for scheduled, or `creationTime + durationMinutes` for "open_door.")
* `durationMinutes`: `Number` (Explicit duration for "open_door" activities, otherwise derived from start/end times.)
* `targetAudience`: `[String]` ("oldPals", "friends", "newFriends", "everyone" - refers to the *owner's* social circles.)
* `childrenWelcome`: `Boolean` (Default: `true`)
* `active`: `Boolean` (`true` if currently available/upcoming, `false` if expired or deactivated.)

---

### **2. Backend Endpoints (API)**

These functions will operate on your chosen database (e.g., KV store, NoSQL, SQL) and represent the core API for the frontend.

#### **2.1. User Management**

* **`POST /api/users/register`**
    * **Description:** Creates a new user record.
    * **Request Body:** `{name: String, location: {lat: Number, lon: Number}, transportModes: [String]}`
    * **Response:** `{userId: String}`
* **`PUT /api/users/{userId}`**
    * **Description:** Updates specific user fields (e.g., location, transport modes, `basicScheduleText`).
    * **Request Body:** `{updates: Object}` (Partial user data)
    * **Response:** `{status: "success" | "error"}`
* **`POST /api/users/{userId}/friends`**
    * **Description:** Adds `friendId` to `userId`'s `newFriends` list. This is a one-way addition for v1.
    * **Request Body:** `{friendId: String}`
    * **Response:** `{status: "success" | "error"}`
* **`PUT /api/users/{userId}/friends/{friendId}/circle`**
    * **Description:** Changes the intimacy level of a friend for the `userId`.
    * **Request Body:** `{newCircle: "oldPals" | "friends" | "newFriends"}`
    * **Response:** `{status: "success" | "error"}`

#### **2.2. Activity Management (Broadcasting)**

* **`POST /api/activities`**
    * **Description:** Creates and stores a new activity. If `durationMinutes` is provided for "open_door," the backend will manage scheduling its deactivation (e.g., via a cron job or scheduled task).
    * **Request Body:** `{ownerId: String, type: String, title: String, location: {lat: Number, lon: Number}|String, startTime?: DateTime, endTime?: DateTime, durationMinutes?: Number, targetAudience: [String], childrenWelcome: Boolean}`
    * **Response:** `{activityId: String}`
* **`PUT /api/activities/{activityId}/deactivate`**
    * **Description:** Marks an activity as inactive. Called manually or by scheduled tasks for expired activities.
    * **Response:** `{status: "success" | "error"}`

#### **2.3. Activity Discovery (Viewing Options)**

* **`GET /api/activities/options?userId={viewerId}`**
    * **Description:** Retrieves and ranks activities relevant to the `viewerId`.
    * **Process:**
        1.  Retrieve `viewerId`'s `location`, `transportModes`, and `socialCircles`.
        2.  Filter all `active` activities:
            * `ownerId` is not `viewerId`.
            * `viewerId` is within the activity's `targetAudience` (based on `ownerId`'s `socialCircles` for `viewerId`).
            * Scheduled activities are in the future.
            * **Simplified Feasibility:** Calculate approximate travel time (e.g., `distance / average_speed_for_mode`) for `viewerId` to `activity.location`. Filter out options where travel time exceeds a threshold (e.g., 30-45 mins for a walk/bike).
        3.  **Ranking:**
            * Primary: **Distance** (closest first).
            * Secondary: **Social Circle intimacy** (Old Pals > Friends > New Friends).
            * Tertiary: **Time** (sooner activities first).
    * **Response:** `Array<{activityId: String, ownerName: String, title: String, type: String, socialCircleTag: String, timeInfo: String, travelInfo: String}>`
        * `ownerName` derived from `ownerId`.
        * `socialCircleTag`: e.g., "Old Pal", "Friend", "New Friend".
        * `timeInfo`: e.g., "Leaving in 15 mins", "Open until 5 PM".
        * `travelInfo`: e.g., "15 min bike", "Walk 5 min".

---

### **3. User Interface (UI) Specification**

The UI will provide clear flows for interaction with the backend API.

#### **3.1. Authentication (Basic OAuth Concept)**

* **Flow:**
    1.  **Initial Screen:** "Sign In with Google" button.
    2.  **User Action:** Taps button.
    3.  **System Action:** Redirects to a simplified OAuth provider (or a placeholder for Google OAuth).
    4.  **Backend Callback:** Upon successful authentication, a designated backend endpoint receives user ID and potentially a session token. This endpoint persists the `userId` in your database if new, and securely sends the `userId` back to the client.
    5.  **Client Action:** The client stores the `userId` locally (e.g., in `localStorage`) for subsequent API calls.
* **Purpose for v1:** Primarily user identification and secure session, not importing external data like Google Calendar.

#### **3.2. Home Screen**

* **Purpose:** Display available activities and provide quick access to broadcasting.
* **Layout:**
    * **Header:** "OUT" app title.
    * **Main Content:** A vertically scrollable list of activity "Options."
        * Each **Option Card** displays:
            * `title` (e.g., "Storytime at Library")
            * `ownerName` (e.g., "with Kate and Nick")
            * Small `socialCircleTag` (e.g., "Old Pal")
            * `timeInfo` (e.g., "Leaving in 15 mins", "Open until 5 PM")
            * `travelInfo` (e.g., "15 min bike", "Walk 5 min")
    * **Footer:** Prominent "Create Activity" button.
* **Interactions:**
    * **Load:** Calls `GET /api/activities/options?userId={currentUserId}` to populate the list.
    * **Refresh:** Pull-to-refresh or a refresh button to re-call `GET /api/activities/options`.
    * **"Create Activity" Button:** Navigates to the "Create Activity Flow."

#### **3.3. Create Activity Flow**

* **Purpose:** Allows users to broadcast "Open Door" or "Bat Signal" activities.
* **Entry:** "Create Activity" button on Home Screen.
* **Steps:**
    1.  **Choose Type Screen:**
        * **UI:** Buttons/radio selectors for "Open Door," "Scheduled Outing," "Help Request."
        * **Action:** User selects a type, navigates to next step.
    2.  **Details Input Screen (adapts per type):**
        * **"Open Door" UI:**
            * `Input:` "What's happening?" (Text field for `title`)
            * `Input:` "How long will your door be open?" (e.g., "2 hours," "Until 3 PM") - maps to `durationMinutes`. Defaults to 2 hours if left blank.
            * `Display:` User's current `location` (read-only).
            * `Toggle:` "Children Welcome?" (maps to `childrenWelcome`)
            * `Button:` "Next"
        * **"Scheduled Outing" UI:**
            * `Input:` "Activity Title?" (Text field for `title`)
            * `Input:` "Location (Address or Name):" (Text field for `location`)
            * `Picker:` Date picker for `startTime` date.
            * `Picker:` Time picker for `startTime` time.
            * `Picker:` Optional time picker for `endTime` (defaults to `startTime + 2 hours`).
            * `Toggle:` "Children Welcome?"
            * `Button:` "Next"
        * **"Help Request" UI:**
            * `Input:` "What help do you need?" (Text field for `title`)
            * `Input:` "When do you need help?" (Free text for `description`, *not* parsed for v1 timing).
            * `Display:` User's current `location` (read-only).
            * `Toggle:` "Children Welcome (if they're joining you)?"
            * `Button:` "Next"
    3.  **Audience Selection Screen:**
        * **UI:** Radio buttons/checkboxes for `targetAudience`: "Old Pals Only," "Friends (includes Old Pals)," "New Friends (includes Friends & Old Pals)," "Everyone (includes New Friends & all others)."
        * **Button:** "Broadcast Activity"
    * **Action (Final Step):** Calls `POST /api/activities` with collected data.
    * **Success:** Displays a confirmation and navigates back to Home Screen.

#### **3.4. Friend Management Flow**

* **Purpose:** Add new friends and organize existing ones into social circles.
* **Entry:** A "Friends" or "Circles" button/tab (e.g., from a settings/profile menu).
* **Screens:**
    1.  **Friend List Screen:**
        * **Header:** "My Circles"
        * **Content:** List of friends, grouped by "Old Pals," "Friends," "New Friends" with each friend's `name`.
        * **Button:** "Add New Friend."
    2.  **Add New Friend Screen:**
        * **Input:** "Friend's Name or Email/ID:" (Text field).
        * **Button:** "Add Friend"
        * **Action:** Calls `POST /api/users/{currentUserId}/friends` (where `friendId` is looked up/created by backend).
        * **Success:** Returns to Friend List, new friend appears in "New Friends."
    3.  **Move Friend to Circle Screen (triggered by tapping existing friend):**
        * **UI:** Pop-up or new screen with radio buttons for "Old Pals," "Friends," "New Friends."
        * **Button:** "Save"
        * **Action:** Calls `PUT /api/users/{currentUserId}/friends/{friendId}/circle`.
        * **Success:** Returns to Friend List with updated circle.

#### **3.5. Schedule Delineation**

* **Purpose:** Allow users to input their general availability (for future use).
* **Entry:** "My Schedule" button/tab (e.g., from a settings/profile menu).
* **UI:**
    * **Header:** "My General Schedule"
    * **Text Area:** Multi-line text input for `basicScheduleText`.
    * **Instructions:** "Describe your typical schedule (e.g., 'Work 9-5 M-F', 'Baby naps 1-3 PM daily')."
    * **Button:** "Save Schedule"
* **Action:** Calls `PUT /api/users/{currentUserId}` with `{basicScheduleText: inputContent}`.

