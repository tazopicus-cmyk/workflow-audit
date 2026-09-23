Free Ops Automation Checklist - landing + capture upload
Built 2026-09-23 by Ana for HostGator path /ops-checklist/

This is a separate magnet from Free Social Media Audit. Do not mix those files.

FILES
- index.html
- thank-you.html
- styles.css
- capture.php
- config.sample.php (copy to config.php on the server)
- deliver-email.html
- checklist.md
- .htaccess (blocks web fetch of config.php)
- inbox/.htaccess (blocks web fetch of saved leads)
- README-BOB.txt (this file)

UPLOAD
1. Create a real public folder: /ops-checklist/ (public_html/ops-checklist/)
   WordPress permalinks lose to a physical directory. Same pattern as /slack-audit/ and /role-map/.
2. Unzip ops-checklist-magnet.zip into that folder so the URL is:
   https://tindogdigital.tech/ops-checklist/
   (index.html as default document)
3. Copy config.sample.php to config.php. Paste the live Resend key only.
   Do not commit config.php. Do not put the key in this repo.
4. Confirm .htaccess uploaded (blocks GET of config.php).
5. Confirm PHP can write ops-checklist/inbox/ (0755 is enough if the user is the same as Apache).

HOMEPAGE GOTCHA (do not "fix")
Live WordPress on tindogdigital.tech 301s the bare homepage to tindogbrewing.com
(header: x-redirect-by: WordPress). Role-map and Slack Opportunity Audit still
resolve on tindogdigital.tech.

Keep the header brand href as https://tindogdigital.tech/
Do NOT retarget the brand link to tindogbrewing.com. Visitors who click the
logo will follow WordPress to the brewery home. That is expected until the
WordPress homepage redirect is a separate ticket. Soft nav stays:
- https://tindogdigital.tech/role-map/
- https://tindogdigital.tech/slack-audit/

RESEND
- From: Ana at Tin Dog Digital <ana@tindogdigital.tech>
- Reply-To: ana@tindogdigital.tech
- Subject: Your Free Ops Automation Checklist
- Body: deliver-email.html (TRACE letters + soft CTAs)
- Attachment: ops-automation-checklist.md
- Optional BCC: ERIC.ROUGH@TINDOGBREWING.COM (hardcoded default in capture.php if LEAD_NOTIFY_EMAIL is unset)
- Domain / From address must already be verified in Resend. If send fails, capture.php still saves the lead in inbox/ and the visitor sees ?error=send.

CRITICAL PATH
Browser form -> capture.php -> save inbox (best effort) -> Resend.
No Cursor webhook. No Grok Bot. No MailerLite. No Zapier.

MAILERLITE / ZAPIER (later, separate ops list)
Do not wire MailerLite or Zapier on this path yet. HostGator + Resend is the
launch path. If Ops later wants a MailerLite group or a Zapier "new checklist
lead" zap, that is a separate list. Inbox JSON/JSONL on the server is the
backup if Resend is late.

SMOKE
Use Eric's address (ERIC.ROUGH@TINDOGBREWING.COM or the address he names).
1. Open https://tindogdigital.tech/ops-checklist/
2. Confirm cream page, Georgia body, forest accent. Header brand is Tin Dog Digital
   and still points at https://tindogdigital.tech/ (do not change it when you
   notice the homepage 301).
3. Nav shows only Role map and Slack Opportunity Audit. No Command Desk.
4. Submit with a blank email: stay on the form with an error.
5. Submit a valid email (name optional). Land on thank-you.html.
6. Confirm email From ana@tindogdigital.tech within about 2 minutes.
7. Confirm TRACE body (T. Track through E. Eliminate), markdown attachment,
   and soft CTAs to role-map + slack-audit only.
8. If delayed more than 15 minutes, escalate to Ana. Check spam, Resend logs,
   then inbox/*.json on the server.

NOT IN THIS UPLOAD
- MailerLite embed
- Zapier
- Command Desk / Setup hard sell
- Free Social Media Audit assets (leave those alone)

SLA (ops)
Checklist email within 2 minutes of confirmed signup. If delayed more than
15 minutes, escalate to Ana. Common failure modes: Resend From unverified,
API key missing in config.php, spam folder, inbox not writable.
