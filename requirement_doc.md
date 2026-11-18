## Master Data

### Wing Master
- Description: Maintain the wings (blocks) of the commercial complex. Units are grouped under wings.
- Data points: WING_CODE, WING_NAME, NO_OF_FLOORS, STATUS (Active/Inactive).
- Business rules: WING_CODE is unique and mandatory. NO_OF_FLOORS must be at least 1. A wing that has Units cannot be deleted, only made Inactive.
- Business actions: Search, Add, Edit, Delete.
- Additional data management: None.

### Unit Master
- Description: Register every unit (shop/office) of the complex with its wing, floor and unit number. It is the anchor for profiles, parking, guests, requests and banner bookings.
- Data points: UNIT_NO (e.g. D715), WING_CODE, FLOOR_NO, UNIT_TYPE (Shop/Office/Showroom/Other), AREA_SQFT, OCCUPANCY_STATUS (Vacant/Owner Used/Given on Rent, display only, maintained from Member Profile), STATUS (Active/Inactive).
- Business rules:
  - UNIT_NO is unique and mandatory.
  - WING_CODE must exist in the Wing Master.
  - FLOOR_NO must be between 0 and the wing's NO_OF_FLOORS.
  - A Unit with a Member Profile cannot be deleted.
- Business actions: Search, Add, Edit, Delete.
- Additional data management: OCCUPANCY_STATUS is updated whenever the Member Profile occupancy changes or a Tenant Profile is added or removed.

### Business Category Master
- Description: List of business types (Lawyer, Chartered Accountant, Doctor, IT Services, Travel Agent, etc.). It is used for directory search and for routing business queries.
- Data points: CATEGORY_CODE, CATEGORY_NAME, DESCRIPTION, STATUS.
- Business rules: CATEGORY_NAME is unique. A category in use by any profile or query cannot be deleted, only made Inactive.
- Business actions: Search, Add, Edit, Delete.
- Additional data management: None.

### Announcement Category Master
- Description: Categories for notices and events (General, Maintenance Shutdown, Security, Meeting, Cultural, Festival, Training).
- Data points: ANNOUNCEMENT_CATEGORY_CODE, NAME, APPLIES_TO (Notice/Event/Both), STATUS.
- Business rules: NAME is unique within APPLIES_TO.
- Business actions: Search, Add, Edit, Delete.
- Additional data management: None.

### Facility Request Category Master
- Description: Categories of concerns a member can raise with the facility team.
- Data points: REQUEST_CATEGORY_CODE (e.g. Plumbing, Electrical, Housekeeping, Lift, Security, Common Area, Other), NAME, TARGET_RESOLUTION_HOURS, STATUS.
- Business rules: NAME is unique. TARGET_RESOLUTION_HOURS is greater than 0 and drives the overdue flag.
- Business actions: Search, Add, Edit, Delete.
- Additional data management: None.

### Facility Team Member Master
- Description: Facility staff and security personnel who are assigned requests and who run the gate.
- Data points: STAFF_CODE, STAFF_NAME, ROLE (Facility Staff/Security Guard/Supervisor), MOBILE_NO, EMAIL, SPECIALISATION (Facility Request Category, optional), STATUS.
- Business rules: STAFF_CODE is unique. MOBILE_NO is mandatory.
- Business actions: Search, Add, Edit, Delete.
- Additional data management: None.

### Guest Purpose Master
- Description: Standard reasons for a guest visit.
- Data points: PURPOSE_CODE, PURPOSE_NAME (Business Meeting, Delivery, Courier, Service/Repair, Interview, Personal, Other), STATUS.
- Business rules: PURPOSE_NAME is unique.
- Business actions: Search, Add, Edit, Delete.
- Additional data management: None.

### Banner Rate Plan Master
- Description: The commercial terms for advertisement banners in the portal carousel. One Active plan applies at a time.
- Data points: PLAN_CODE, PLAN_NAME, RATE_PER_SLOT_PER_MONTH, MIN_MONTHS, MAX_CAROUSEL_SLOTS (banners that can be live on any day), TAX_PCT, SECONDS_PER_BANNER, IMAGE_SIZE_GUIDANCE (text), EFFECTIVE_FROM, STATUS.
- Business rules:
  - RATE_PER_SLOT_PER_MONTH is greater than 0.
  - MIN_MONTHS is at least 1.
  - MAX_CAROUSEL_SLOTS is at least 1.
  - Only one plan can be Active for a given date.
  - A change of rate applies to new bookings only.
- Business actions: Search, Add, Edit, Delete (only if never used in a booking).
- Additional data management: None.

## Units & Profiles

### Member Profile
- Description: The single profile of the owner(s) of a unit, describing the business they run and how members can reach them. Each unit has exactly one Member Profile. It also holds the owner's decision on occupancy (self-use or rent) and on tenant access.
- Data points:
  - Header: UNIT_NO, WING_CODE and FLOOR_NO (display from Unit Master), BUSINESS_NAME, BUSINESS_CATEGORY, BUSINESS_DESCRIPTION, LOGO, CONTACT_PERSON, CONTACT_NO_1, CONTACT_NO_2, EMAIL, WEBSITE, OCCUPANCY_TYPE (Owner Used/Given on Rent), SHOW_IN_DIRECTORY (Yes/No), TENANT_LOGIN_ALLOWED (Yes/No), ALLOW_TENANT_TO_UPDATE_PROFILE (Yes/No), SHOW_TENANT_IN_DIRECTORY (Yes/No), PROFILE_STATUS (Active/Inactive).
  - Other Categories (lines): CATEGORY_CODE (additional business categories beyond the primary BUSINESS_CATEGORY; no duplicates, not equal to the primary).
  - Joint Owners (lines): OWNER_NAME, OWNER_MOBILE, OWNER_EMAIL, IS_PRIMARY_OWNER, LOGIN_ENABLED.
- Business rules:
  - Only one Member Profile can exist per UNIT_NO.
  - At least one Joint Owner line is required, and exactly one line has IS_PRIMARY_OWNER = Yes.
  - OWNER_EMAIL is unique across all owners. A person who owns several units is entered on each unit's profile.
  - BUSINESS_NAME, CONTACT_NO_1 and EMAIL are mandatory. BUSINESS_CATEGORY and CONTACT_NO_2 are optional.
  - Contact numbers must be valid phone numbers and CONTACT_NO_1 must differ from CONTACT_NO_2. EMAIL must be a valid address.
  - The tenant-related flags (TENANT_LOGIN_ALLOWED, ALLOW_TENANT_TO_UPDATE_PROFILE, SHOW_TENANT_IN_DIRECTORY) are enabled only when OCCUPANCY_TYPE = Given on Rent. They are reset to No otherwise.
  - OCCUPANCY_TYPE cannot be changed from Given on Rent to Owner Used while the Tenant Profile is Active. The owner must first Remove Tenant.
  - An owner can view and edit only the profile of a unit where they are a Joint Owner. Management can add and edit any profile.
  - SHOW_IN_DIRECTORY = No hides the business from the Business Directory but not from the unit lookup of management and security.
- Business actions: Search, Add, Edit, Delete (management only, when the unit has no open requests or Active tenant), Add Tenant (opens Tenant Profile for the unit), View Tenant Profile.
- Additional data management: On save, Unit Master OCCUPANCY_STATUS is updated (Owner Used / Given on Rent). Changing the tenant flags is applied immediately to the Tenant Profile (login enabled, edit rights, directory visibility). Management creating a profile sends a welcome email to each Joint Owner who has LOGIN_ENABLED = Yes.

### Tenant Profile
- Description: The profile of the tenant business occupying a rented unit. It is created by the owner (or management) and may be maintained by the tenant when the owner allows it. Only one Tenant Profile exists per unit.
- Data points: UNIT_NO, TENANT_COMPANY_NAME, BUSINESS_CATEGORY, BUSINESS_DESCRIPTION, LOGO, CONTACT_PERSON, CONTACT_NO_1, CONTACT_NO_2, TENANT_EMAIL, LEASE_START_DATE, LEASE_END_DATE, SHOW_IN_DIRECTORY, LOGIN_ENABLED, CAN_UPDATE_PROFILE (display, from the owner's flag), TENANT_STATUS (Active/Removed), ADDED_BY (defaults to :user_email), REMOVED_ON, REMOVAL_REASON, OWNER_BUSINESS_NAME (display), OWNER_CONTACT_NO_1 (display).
- Other Categories (lines): CATEGORY_CODE (additional business categories beyond the primary BUSINESS_CATEGORY; no duplicates, not equal to the primary).
- Business rules:
  - A Tenant Profile can be added only when the unit's Member Profile has OCCUPANCY_TYPE = Given on Rent.
  - One Tenant Profile per UNIT_NO. A new tenant after a removal is entered by editing the Removed record and re-activating it. The previous details are overwritten.
  - TENANT_COMPANY_NAME, CONTACT_PERSON, CONTACT_NO_1 and TENANT_EMAIL are mandatory. TENANT_EMAIL is unique across tenants and owners.
  - LEASE_END_DATE must not be before LEASE_START_DATE.
  - LOGIN_ENABLED can be Yes only if the owner's TENANT_LOGIN_ALLOWED = Yes. SHOW_IN_DIRECTORY can be Yes only if SHOW_TENANT_IN_DIRECTORY = Yes.
  - The tenant can edit this profile only if the owner's ALLOW_TENANT_TO_UPDATE_PROFILE = Yes. The tenant can never edit the Member Profile, the Unit or the tenant flags, and can never remove themselves.
  - Only the unit's owners or management can Remove Tenant. Removal needs a REMOVAL_REASON and sets TENANT_STATUS = Removed, LOGIN_ENABLED = No and SHOW_IN_DIRECTORY = No.
- Business actions: Search, Add, Edit, Remove Tenant, Re-activate, View Owner Profile (opens the Member Profile of the same unit in view mode, always shown on the Tenant Profile page).
- Additional data management: On Add or Re-activate a welcome email is sent to TENANT_EMAIL. On Remove Tenant the tenant's open Guest Entries and Facility Requests are left in place for history, and the tenant can no longer sign in. Unit Master OCCUPANCY_STATUS stays Given on Rent.

### Unit Parking
- Description: Record the parking slots held by a unit and the vehicles registered against each slot. A unit can have several slots, and a slot can have several vehicles.
- Data points:
  - Header: PARKING_SLOT_NO, UNIT_NO, SLOT_LOCATION (Basement 1/Basement 2/Podium/Open), SLOT_TYPE (Car/Two-Wheeler), STATUS (Active/Released).
  - Vehicles (lines): VEHICLE_NO, VEHICLE_TYPE (Car/Two-Wheeler/Other), MAKE_MODEL, COLOUR, USED_BY (Owner/Tenant), USER_NAME, USER_MOBILE.
- Business rules:
  - PARKING_SLOT_NO is unique across the complex and belongs to one unit.
  - VEHICLE_NO is mandatory, stored in upper case without spaces, and unique across all active vehicles in the complex.
  - USED_BY = Tenant is allowed only if an Active Tenant Profile exists on the unit.
  - Owners and active tenants of a unit can add and edit parking for their own unit only. Management can edit any.
  - A slot with vehicles cannot be deleted. It must be Released and the vehicles removed.
- Business actions: Search, Add, Edit, Delete, Release Slot.
- Additional data management: None. Vehicles are used by the Vehicle & Parking Register visual.

### Unit Occupancy Overview (V)
- Visualization: Grid with row grouping by wing and totals.
- Criteria: Wing, Floor, Occupancy Status, Profile Completed (Yes/No). Default: all wings.
- Data points: UNIT_NO, WING_CODE, FLOOR_NO, OWNER names, BUSINESS_NAME, OCCUPANCY_STATUS, TENANT_COMPANY_NAME, TENANT_LOGIN_ENABLED, PARKING_SLOT_COUNT, VEHICLE_COUNT, PROFILE_COMPLETED.
- Drill-down: UNIT_NO opens the Member Profile; TENANT_COMPANY_NAME opens the Tenant Profile.

## Business Directory

### Business Directory (V)
- Visualization: Grid, one row per unit, with a search box.
- Criteria: Search text (matches unit number, business or tenant company name, contact person), Business Category, Wing, Floor. Default: all active entries.
- Data points: UNIT_NO, WING_CODE, FLOOR_NO, DISPLAY_NAME, CATEGORY, CONTACT_PERSON, CONTACT_NO_1, CONTACT_NO_2, EMAIL, OCCUPANCY_LABEL.
- Business rules:
  - DISPLAY_NAME is the owner's BUSINESS_NAME when the unit is Owner Used.
  - When the unit is Given on Rent, the Tenant is Active and the owner has set SHOW_TENANT_IN_DIRECTORY = Yes and the tenant's SHOW_IN_DIRECTORY = Yes, DISPLAY_NAME is TENANT_COMPANY_NAME followed by "(Tenant)". The tenant's contacts and category are shown.
  - When the unit is rented but the tenant is not shown, the owner's profile is displayed.
  - A search for a unit number such as D715 returns that unit's entry.
  - Entries with SHOW_IN_DIRECTORY = No are excluded.
  - Phone numbers are shown as tap-to-call links, and EMAIL as a mail link.
- Drill-down and hyperlinks: DISPLAY_NAME opens the Tenant Profile (for "(Tenant)" rows) or the Member Profile in view mode. The Tenant Profile page offers View Owner Profile.

## Notices & Events

### Notice
- Description: Management publishes notices to members and tenants.
- Data points: NOTICE_NO (auto), TITLE, ANNOUNCEMENT_CATEGORY, NOTICE_BODY, PUBLISH_DATE, EXPIRY_DATE, AUDIENCE (All Members & Tenants/Owners Only/Specific Wing), WING_CODE (when Specific Wing), IS_IMPORTANT, ATTACHMENT, STATUS (Draft/Published/Withdrawn), PUBLISHED_BY (defaults to :user_email).
- Business rules:
  - TITLE, ANNOUNCEMENT_CATEGORY, NOTICE_BODY and PUBLISH_DATE are mandatory.
  - EXPIRY_DATE must not be before PUBLISH_DATE.
  - WING_CODE is mandatory only for AUDIENCE = Specific Wing.
  - A Published notice cannot be deleted, only Withdrawn. Only Draft notices can be deleted.
  - A notice shows on the Notice Board from PUBLISH_DATE until EXPIRY_DATE (or until withdrawn if no expiry).
  - Only management can add, edit, publish or withdraw notices.
- Business actions: Search, Add, Edit, Delete (Draft only), Publish, Withdraw.
- Additional data management: On Publish, an in-app notification and email are sent to the intended audience (owners, active tenants with login, filtered by wing where applicable).

### Event
- Description: Management announces events and happenings in the complex.
- Data points: EVENT_NO (auto), TITLE, ANNOUNCEMENT_CATEGORY, DESCRIPTION, VENUE, START_DATE_TIME, END_DATE_TIME, ORGANISER, ORGANISER_CONTACT_NO, AUDIENCE, WING_CODE, EVENT_IMAGE, STATUS (Draft/Published/Cancelled), CANCELLATION_REASON.
- Business rules:
  - TITLE, VENUE, START_DATE_TIME and END_DATE_TIME are mandatory.
  - END_DATE_TIME must be after START_DATE_TIME.
  - START_DATE_TIME cannot be in the past when Published.
  - Cancel needs CANCELLATION_REASON.
  - Only management can add, edit, publish or cancel events.
  - An event is shown as Completed once its end time has passed (derived, not stored).
- Business actions: Search, Add, Edit, Delete (Draft only), Publish, Cancel.
- Additional data management: On Publish or Cancel, an in-app notification and email go to the audience.

### Notice Board (V)
- Visualization: Feeds.
- Criteria: Category, Wing, Show Expired (default No), Important Only. Default: current published notices for the user's audience, newest first and important ones pinned on top.
- Data points: TITLE, CATEGORY, PUBLISH_DATE, EXPIRY_DATE, IS_IMPORTANT, short body.
- Drill-down: Item opens the full Notice with attachment.

### Event Calendar (V)
- Visualization: Calendar with month, week and list views.
- Criteria: Month (default current), Category, Show Cancelled (default No).
- Data points: TITLE, START_DATE_TIME, END_DATE_TIME, VENUE, CATEGORY, STATUS.
- Drill-down: Event opens the full Event details.

## Business Queries

### Business Query
- Description: A member or tenant asks the community for a business service (e.g. "Does anyone know a lawyer?"). The query is forwarded automatically to every business in the chosen category, who can respond with their contact details.
- Data points:
  - Header: QUERY_NO (auto), QUERY_DATE (default today), RAISED_BY_UNIT_NO (default from the user's unit), RAISED_BY_NAME, RAISED_BY_EMAIL (defaults to :user_email), TARGET_BUSINESS_CATEGORY, SUBJECT, DESCRIPTION, STATUS (Open/Closed), CLOSURE_REMARK, CLOSED_ON.
  - Recipients (lines, system generated): UNIT_NO, BUSINESS_NAME, RECIPIENT_EMAIL, FORWARDED_ON, VIEWED (Yes/No).
  - Responses (lines): RESPONSE_DATE, RESPONDER_UNIT_NO, RESPONDER_BUSINESS_NAME, RESPONSE_TEXT, RESPONDER_CONTACT_NO.
- Business rules:
  - TARGET_BUSINESS_CATEGORY, SUBJECT and DESCRIPTION are mandatory.
  - On the first save, Recipients are generated from every directory-visible profile whose BUSINESS_CATEGORY matches. The owner's profile is used for Owner Used units, and the Active tenant with login for rented units where the tenant is shown. The raiser's own unit is excluded.
  - If no recipient is found, a warning is shown and the query is still saved.
  - TARGET_BUSINESS_CATEGORY cannot be changed after the first save.
  - Only recipients and the raiser can add Responses. RESPONDER_CONTACT_NO defaults from the responder's profile.
  - Only the raiser or management can Close a query. A Closed query accepts no further responses.
  - The raiser sees their own queries and all responses. Recipients see queries forwarded to them.
- Business actions: Search, Add, Edit (Open, raiser only), Delete (no responses, raiser or management), Add Response, Close, Reopen (raiser or management).
- Additional data management: On first save an email and notification are sent to every recipient with the query, and the raiser's contact details. On each new Response, the raiser is notified.

### Queries Received (V)
- Visualization: Grid.
- Criteria: Status (default Open), Date range (default last 30 days), Category.
- Data points: QUERY_NO, QUERY_DATE, RAISED_BY_UNIT_NO, SUBJECT, TARGET_BUSINESS_CATEGORY, STATUS, RESPONSE_COUNT, I_HAVE_RESPONDED. Shows only queries forwarded to the signed-in user's unit, matched by :user_email.
- Drill-down: QUERY_NO opens the Business Query.

## Ad Banners & Billing

### Banner Booking
- Description: Capture a request for a monthly banner slot in the portal's carousel, with a simple billing flow. Management approves the banner, raises the invoice, and records payment. A banner goes live when it is Approved and Paid and its dates are current.
- Data points:
  - Booking: BOOKING_NO (auto), BOOKING_DATE, ADVERTISER_TYPE (Member/Tenant/External), UNIT_NO, ADVERTISER_NAME, CONTACT_NO, EMAIL, BANNER_TITLE, BANNER_IMAGE, CLICK_URL, START_DATE, NO_OF_MONTHS, END_DATE (calculated), BOOKING_STATUS (Requested/Approved/Rejected/Cancelled), REJECTION_REASON.
  - Billing: RATE_PER_MONTH (default from the Active Banner Rate Plan), AMOUNT, TAX_PCT, TAX_AMOUNT, TOTAL_AMOUNT, INVOICE_NO, INVOICE_DATE.
  - Payment: PAYMENT_STATUS (Unpaid/Paid), PAYMENT_MODE (Cash/Cheque/Bank Transfer/UPI), PAYMENT_REFERENCE, PAYMENT_DATE, RECEIVED_BY.
  - Display: DISPLAY_STATE (Scheduled/Live/Ended, derived).
- Business rules:
  - NO_OF_MONTHS must be at least the plan's MIN_MONTHS and a whole number.
  - END_DATE = START_DATE plus NO_OF_MONTHS months minus one day. START_DATE cannot be in the past.
  - UNIT_NO is mandatory for Member and Tenant advertisers and must exist in the Unit Master. ADVERTISER_NAME, CONTACT_NO, EMAIL, BANNER_TITLE and BANNER_IMAGE are mandatory.
  - CLICK_URL, if given, must be a valid web address.
  - AMOUNT = RATE_PER_MONTH × NO_OF_MONTHS. TAX_AMOUNT = AMOUNT × TAX_PCT / 100. TOTAL_AMOUNT = AMOUNT + TAX_AMOUNT.
  - On Approve, the number of Approved bookings overlapping any day of the period must stay below MAX_CAROUSEL_SLOTS. If not, approval is blocked and the next available start date is shown.
  - Approve generates INVOICE_NO and INVOICE_DATE. A booking can be recorded as Paid only after Approval.
  - A booking is Live only when BOOKING_STATUS = Approved, PAYMENT_STATUS = Paid and today falls between START_DATE and END_DATE.
  - After Approval only the payment fields and BANNER_IMAGE can be edited (the banner image can be replaced after booking and payment). Cancel is allowed before START_DATE. Refunds are settled outside the system.
  - Members and tenants see and edit their own bookings. Management can book for anyone, and approves, rejects and records payments.
- Business actions: Search, Add, Edit, Delete (Requested only), Approve, Reject, Cancel, Record Payment, Print Invoice.
- Additional data management: On Approve, the advertiser is emailed the invoice details. On Record Payment, the banner is made eligible for the carousel and the advertiser is notified.

### Banner Carousel (V)
- Visualization: Html template rendered as an auto-rotating carousel strip, placed at the top of every portal page (all pages, dashboards and the home page).
- Criteria: Today's date (system). No user input.
- Data points: BANNER_IMAGE, BANNER_TITLE, CLICK_URL, DISPLAY_ORDER (by START_DATE, then BOOKING_NO), SECONDS_PER_BANNER (from the Active Banner Rate Plan).
- Business rules: Shows only Live bookings. Clicking a banner opens CLICK_URL in a new tab. Banners rotate automatically with manual previous and next controls. The strip is hidden when no banner is Live.

### Banner Invoice (R)
- Layout type: Single-document print/PDF per booking, A4 portrait.
- Criteria: BOOKING_NO (mandatory).
- Grouping: None. One document per booking.
- Layout: Header with the complex's name and address and the INVOICE title. Bill-to block (ADVERTISER_NAME, UNIT_NO, CONTACT_NO, EMAIL). INVOICE_NO and INVOICE_DATE.
- Columns: Description (Banner slot, BANNER_TITLE), Period (START_DATE to END_DATE), NO_OF_MONTHS, RATE_PER_MONTH, AMOUNT.
- Totals: AMOUNT, TAX_AMOUNT, TOTAL_AMOUNT, PAYMENT_STATUS with PAYMENT_MODE, PAYMENT_REFERENCE and PAYMENT_DATE when Paid.
- Footer: Terms (the banner is displayed only after payment) and a management signature block.

### Banner Bookings & Collections (V)
- Visualization: Grid with totals.
- Criteria: Date range on START_DATE (default current financial year), Booking Status, Payment Status, Advertiser Type.
- Data points: BOOKING_NO, ADVERTISER_NAME, UNIT_NO, START_DATE, END_DATE, NO_OF_MONTHS, TOTAL_AMOUNT, BOOKING_STATUS, PAYMENT_STATUS, DISPLAY_STATE. Totals: billed and received.
- Drill-down: BOOKING_NO opens the Banner Booking.

### Banner Slot Availability (V)
- Visualization: Stacked-Column-Chart by month, with the capacity limit shown as a reference value.
- Criteria: Months ahead (default next 6 months).
- Data points: month vs Approved slots booked and slots available (MAX_CAROUSEL_SLOTS minus booked).
- Drill-down: A month column opens Banner Bookings & Collections for that month.

## Guest Entry & Security

### Guest Entry
- Description: Record a guest coming into the building. A member or tenant can pre-register a guest and receive a pass code and QR, or the security desk can register a walk-in guest who must be approved by the unit. Security checks the guest in and out.
- Data points: GUEST_ENTRY_NO (auto), ENTRY_TYPE (Pre-Registered/Walk-In), GUEST_NAME, GUEST_MOBILE, NO_OF_PERSONS, GUEST_COMPANY, PURPOSE (Guest Purpose Master), UNIT_NO (unit visited), PERSON_TO_MEET, EXPECTED_DATE, VALID_FROM_TIME, VALID_TO_TIME, VEHICLE_NO, ID_PROOF_TYPE, ID_PROOF_NO, PASS_CODE (auto), PASS_QR (auto), REGISTERED_BY (defaults to :user_email), STATUS (Expected/Awaiting Approval/Approved/Rejected/Checked In/Checked Out/Cancelled), APPROVED_VIA (App/Phone), APPROVED_BY, CHECK_IN_TIME, CHECKED_IN_BY, CHECK_OUT_TIME, SECURITY_REMARK.
- Business rules:
  - GUEST_NAME, GUEST_MOBILE, PURPOSE, UNIT_NO and NO_OF_PERSONS (at least 1) are mandatory.
  - Pre-Registered: EXPECTED_DATE cannot be in the past and VALID_TO_TIME must be after VALID_FROM_TIME. STATUS starts as Expected and a unique PASS_CODE and PASS_QR are generated on save.
  - Walk-In: ID_PROOF_TYPE and ID_PROOF_NO are mandatory, EXPECTED_DATE is today and STATUS starts as Awaiting Approval.
  - Only a member or an active tenant of that UNIT_NO can Approve or Reject a Walk-In entry. Security can record the approval as APPROVED_VIA = Phone with the name of the person who approved.
  - Check In is allowed only for Expected (on the expected date) or Approved entries. A check-in outside the valid time window or on a different date needs a SECURITY_REMARK.
  - CHECK_OUT_TIME must be after CHECK_IN_TIME. Check Out is allowed only for Checked In entries.
  - Rejected, Checked Out and Cancelled entries are locked. An Expected entry that is past its date is shown as Expired in lists.
  - Members and tenants see and manage only their own unit's entries. Security can search all entries and see today's expected guests.
- Business actions: Search, Add, Edit (Expected only), Delete (Expected only), Cancel, Approve, Reject, Scan QR Code, Check In, Check Out.
- Additional data management: On Walk-In registration the unit's owners and active tenant are notified for approval. On Pre-Registration the pass code is shown for sharing with the guest. On Check In and Check Out, the unit contacts are notified.

### Gate Check-In (U)
- Base transaction: Guest Entry. It edits an existing Pre-Registered entry (Expected to Checked In), or adds a new Walk-In entry. An existing entry is found by scanning the PASS_QR or typing the PASS_CODE.
- Users and device: Security guards at the gate on a handheld scanner or phone.
- Steps:
  1. Choose the action: Scan Pass or Walk-In Guest.
  2. Scan Pass: scan the QR (it contains the PASS_CODE) or type the 6-character code. The guest, unit, purpose, expected date and time window are shown.
  3. Walk-In: select the unit (typed UNIT_NO), then enter GUEST_NAME, GUEST_MOBILE, NO_OF_PERSONS, PURPOSE, VEHICLE_NO, ID_PROOF_TYPE and ID_PROOF_NO.
  4. Walk-In: submit for approval. The wizard waits for the resident's Approve or Reject, or lets the guard choose Approved by Phone and type the approver's name.
  5. Review the guest summary and confirm.
  6. Save as Checked In (the transaction's own save applies all rules).
- Exceptions and loops:
  - Pass not found: the wizard offers to retype or switch to Walk-In.
  - Pass for another date or outside the time window: the guard must enter a SECURITY_REMARK to continue.
  - Pass already used or cancelled: the wizard stops and shows the status.
  - Walk-In Rejected: the wizard ends with the entry saved as Rejected.
  - After saving, the wizard returns to step 1 for the next guest.

### Guest Log (V)
- Visualization: Grid with totals.
- Criteria: Date range (default today), Status, Unit No, Entry Type, Guest Name or Mobile.
- Data points: GUEST_ENTRY_NO, GUEST_NAME, GUEST_MOBILE, UNIT_NO, PURPOSE, ENTRY_TYPE, STATUS, CHECK_IN_TIME, CHECK_OUT_TIME, DURATION_MINUTES, VEHICLE_NO. Totals: number of guests.
- Drill-down: GUEST_ENTRY_NO opens the Guest Entry. A preset "Inside Now" shows Checked In guests with no check-out.

### Vehicle & Parking Register (V)
- Visualization: Grid.
- Criteria: Vehicle No (partial), Unit No, Parking Slot, Wing.
- Data points: VEHICLE_NO, VEHICLE_TYPE, MAKE_MODEL, PARKING_SLOT_NO, SLOT_LOCATION, UNIT_NO, DISPLAY_NAME (business or tenant name), USER_NAME, USER_MOBILE.
- Drill-down: UNIT_NO opens the Member Profile in view mode.

### Daily Guest Register (R)
- Layout type: Tabular log, A4 landscape, printed by security at end of shift.
- Criteria: Date (mandatory), Shift (Day/Night, optional).
- Grouping: Grouped by Wing, then Unit, with a count of guests per wing.
- Columns: GUEST_ENTRY_NO, GUEST_NAME, GUEST_MOBILE, NO_OF_PERSONS, UNIT_NO, PURPOSE, ENTRY_TYPE, VEHICLE_NO, CHECK_IN_TIME, CHECK_OUT_TIME, CHECKED_IN_BY.
- Totals: Guests per wing and grand total, plus the number still inside. Footer with a security supervisor signature block.

## Facility Requests

### Facility Request
- Description: A member or tenant raises a concern with the facility team, and the team assigns, works on, and resolves it, with the raiser kept informed.
- Data points:
  - Header: REQUEST_NO (auto), REQUEST_DATE_TIME (default now), UNIT_NO (default from the user's unit), RAISED_BY_NAME, RAISED_BY_EMAIL (defaults to :user_email), RAISED_BY_CONTACT_NO, REQUEST_CATEGORY, PRIORITY (Low/Medium/High/Urgent), LOCATION_DETAIL, DESCRIPTION, ATTACHMENT, ASSIGNED_TO (Facility Team Member), TARGET_DATE_TIME (calculated), STATUS (Open/Assigned/In Progress/Resolved/Closed/Cancelled), RESOLUTION_NOTE, RESOLVED_ON, CLOSED_ON, IS_OVERDUE (derived).
  - Updates (lines): UPDATE_DATE_TIME, UPDATED_BY, STATUS, REMARK.
- Business rules:
  - UNIT_NO, REQUEST_CATEGORY, PRIORITY and DESCRIPTION are mandatory.
  - TARGET_DATE_TIME = REQUEST_DATE_TIME + the category's TARGET_RESOLUTION_HOURS. Overdue is flagged when it passes and the status is not Resolved or Closed.
  - Allowed status flow: Open → Assigned → In Progress → Resolved → Closed. A Resolved request can be Reopened (back to In Progress) by the raiser or management. Open or Assigned requests can be Cancelled.
  - ASSIGNED_TO is mandatory to move to Assigned and must be an active Facility Team Member. RESOLUTION_NOTE is mandatory to move to Resolved.
  - Every status change adds an Updates line.
  - Members and tenants see only their unit's requests and can Cancel, Reopen, Close and add comments. The facility team and management see all and perform Assign, Start Work and Resolve.
- Business actions: Search, Add, Edit (Open only), Delete (Open only, no updates), Assign, Start Work, Resolve, Close, Reopen, Cancel.
- Additional data management: Each status change notifies the raiser by in-app notification and email. Assignment notifies the Facility Team Member. A request in the Security category also notifies the Supervisor.

### Facility Request Register (V)
- Visualization: Grid with totals.
- Criteria: Date range (default last 30 days), Status (default open states), Category, Priority, Wing, Assigned To, Overdue Only.
- Data points: REQUEST_NO, REQUEST_DATE_TIME, UNIT_NO, REQUEST_CATEGORY, PRIORITY, STATUS, ASSIGNED_TO, TARGET_DATE_TIME, IS_OVERDUE, age in hours.
- Drill-down: REQUEST_NO opens the Facility Request.

### Facility Requests by Category and Status (V)
- Visualization: Stacked-Column-Chart.
- Criteria: Date range (default current month), Wing.
- Data points: REQUEST_CATEGORY on the axis, count of requests stacked by STATUS.
- Drill-down: A segment opens Facility Request Register filtered by that category and status.

## Dashboards

### Member Dashboard (D)
- Role: Owner / Member.
- Criteria: Unit (defaults to the signed-in owner's unit, selectable if they own several units).
- Visuals:
  - Banner Carousel (V), as the top strip.
  - Card: My Open Facility Requests. Data: count by unit. Drills to Facility Request Register.
  - Card: Open Business Queries For Me. Data: count from Queries Received. Drills to Queries Received.
  - Card: Guests Expected Today. Data: count of Expected and Approved entries for the unit. Drills to Guest Log.
  - Card: Tenant Status. Data: Tenant company name or "Owner Used". Drills to the Tenant Profile.
  - Feeds: Latest Notices (Notice Board). Drills to the Notice.
  - Calendar (compact month): Upcoming Events (Event Calendar). Drills to the Event.
  - Grid: My Facility Requests (latest 5 active) with status. Drills to the Facility Request.
  - Grid: Guests awaiting my approval (Walk-In entries Awaiting Approval). Drills to the Guest Entry.

### Tenant Dashboard (D)
- Role: Tenant with login.
- Criteria: Unit (fixed to the tenant's unit).
- Visuals:
  - Banner Carousel (V), as the top strip.
  - Card: My Open Facility Requests. Drills to Facility Request Register.
  - Card: Guests Expected Today. Drills to Guest Log.
  - Card: Open Business Queries For Me. Drills to Queries Received.
  - Feeds: Latest Notices for All Members & Tenants. Drills to the Notice.
  - Calendar (compact month): Upcoming Events.
  - Grid: Guests awaiting my approval.
  - Card: Lease End Date (days remaining). Drills to the Tenant Profile.

### Management Dashboard (D)
- Role: Management Committee and administrators.
- Criteria: Date range (default current month), Wing (default all).
- Visuals:
  - Banner Carousel (V), as the top strip.
  - Card: Total Units; Card: Profiles Completed (%); Card: Units Given on Rent; Card: Open Facility Requests; Card: Overdue Requests; Card: Banner Revenue Billed (month) with sparkline of the last 6 months.
  - Doughnut: Occupancy Mix (Owner Used / Given on Rent / Vacant). Drills to Unit Occupancy Overview filtered by occupancy.
  - Stacked-Column: Facility Requests by Category and Status. Drills to Facility Request Register.
  - Column: Banner Slot Availability by month. Drills to Banner Bookings & Collections.
  - Line: Guests per day over the date range, split by Pre-Registered and Walk-In. Drills to Guest Log.
  - Bar: Profiles Missing by Wing (units without a Member Profile). Drills to Unit Occupancy Overview with Profile Completed = No.
  - Grid: Banner Bookings Awaiting Approval. Drills to Banner Booking.
  - Feeds: Notices and Events due this week.

### Facility & Security Dashboard (D)
- Role: Facility Team and Security.
- Criteria: Date (default today), Wing (default all), Assigned To (default all).
- Visuals:
  - Card: Guests Inside Now; Card: Guests Expected Today; Card: Walk-Ins Awaiting Approval; Card: Open Requests; Card: Overdue Requests.
  - Funnel: Request pipeline (Open → Assigned → In Progress → Resolved). Drills to Facility Request Register by status.
  - Bar: Open Requests by Assigned Staff. Drills to Facility Request Register.
  - Pie: Open Requests by Category.
  - Column: Guests by Hour of Day for the selected date. Drills to Guest Log.
  - Grid: Overdue and Urgent Requests. Drills to the Facility Request.
  - Grid: Guests Inside Now. Drills to the Guest Entry.

## Smart Pages

### Portal Home (S)
- Purpose and audience: The welcome page shown after sign-in to every user type. It orients the user and shows the happenings in the complex.
- Key sections:
  - Banner Carousel strip at the top.
  - Hero block: a greeting with the user's name and unit, and a line on the complex.
  - Feature grid of quick-link cards: Business Directory, Notices, Events, Raise a Business Query, Register a Guest, Raise a Facility Request, My Profile, Book a Banner.
  - Embedded visuals: Notice Board (latest 5) and Event Calendar (list view, next 30 days).
  - Callout: Facility desk and security contact numbers (static text maintained by management).
- Inline inputs: One search box, "Search business or unit (e.g. D715)". Pressing Enter opens the Business Directory with the text applied.
- Actions and CTAs: Each card opens its target activity. "Raise a Business Query" opens Business Query in Add mode. "Register a Guest" opens Guest Entry in Add mode. "My Profile" opens the Member Profile (or Tenant Profile for tenants) of the user's unit. Cards for management-only actions (Create Notice, Create Event) are shown only to management.

**Suggested, not built:** maker-checker approval on notices; online payment gateway for banner payments; event RSVP and attendance tracking; satisfaction rating on closed facility requests.