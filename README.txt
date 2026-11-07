DealCart - Settings Backup & Restore Build

Deployment:
1. Keep a copy of your current live site before replacing anything.
2. Deploy the contents of this ZIP to your existing Netlify site only after reviewing the backup.
3. Open the Admin Panel > Settings > Settings Backup & Restore.
4. On the OLD live site's same browser/device, download the settings backup JSON first.
5. On the new build, restore that JSON and verify UPI, WhatsApp, COD, cancellation window and Admin login.

Important:
- This build includes the existing DealCart HTML app and a settings backup/restore feature.
- The ZIP does not contain browser-local live settings from your old site. Export them from the old site first.
- Do not delete old site, customer data, or orders until migration is verified.
- Supabase key is intentionally blank in the source unless configured in Admin settings/environment.
