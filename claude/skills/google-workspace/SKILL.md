---
name: google-workspace
description: Use this skill when Lyndsay asks to search, read, draft, or send emails via Gmail, or when managing Google Calendar events.
---

# Google Workspace Integration

## Authentication

Token: `C:\Users\Courtney Stuart\.openclaw\workspace\google-integration\token.json`

Credentials: `C:\Users\Courtney Stuart\Documents\Coding_Projects\Openclaw_gmail\Google_workspace_credentials\client_secret_546449405397-lh908fm7922plilddvukbjqv555sti6q.apps.googleusercontent.com.json`

Scripts: `C:\Users\Courtney Stuart\.openclaw\workspace\google-integration\`

To use: load credentials + token, create oauth2Client, call googleapis. See existing scripts for the pattern.

If token expires: run `node auth.js` in the google-integration folder, re-authorize in browser. New token.json saves automatically.

## Gmail

- **Account:** lkerwin14@gmail.com
- **Send permission:** Authorized (re-authorized March 2, 2026 with send/compose scope)
- **Search script:** `find-email.js`
- **Send script:** `send-email.js`

### Email Protocol
- Can draft and send emails freely unless Lyndsay says otherwise
- Always include relevant context and be concise

## Calendars

- **Big Calendar** (shared with husband): `ed83id0tl455i1jf5frbmnfe3o@group.calendar.google.com`
- **BLOCK CALENDAR**: `e1j48cl1dat7b12sbaejjm78cs@group.calendar.google.com`
- **Personal**: `lkerwin14@gmail.com`

### Calendar Protocol
For calendar invites and any scheduling actions: **Always show a draft first and wait for Lyndsay's approval before sending.**

## Available Scripts

- `find-email.js` — Search Gmail
- `send-email.js` — Send emails
- `auth.js` — Re-authorize if token expires
- `create-tax-calendar.js` — Tax calendar events
- `find-tax-emails.js` — Search tax-related emails
- `find-ben-tax.js` — Find Ben's tax emails
- `find-erik-submission.js` — Find Erik's submissions
- `find-doc-gathering.js` — Find document gathering emails
- `get-tax-reminders.js` — Get tax reminders
- `get-estimated-tax.js` — Get estimated tax info
