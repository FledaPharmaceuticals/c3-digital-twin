# Deployment

## Target

- App: Fleda C3 Digital Twin
- Preferred domain: `c3twin.fledausa.com`
- Access model: public single-user demo, no login
- Data boundary: no GN/Gummynology code, auth, database, API, customer data, or production data

## Recommended Option

Option A: Streamlit Community Cloud plus DNS CNAME.

Reason: lowest operational burden, fastest path to public medical-research demo, and no server maintenance. This is the best first deployment unless Fleda requires private hosting, custom access logs, or stricter infrastructure control.

## DNS Configuration

Pending confirmation from Fleda:

- DNS provider:
- Subdomain: `c3twin`
- Record type: `CNAME`
- Target: Streamlit app hostname, for example `your-app-name.streamlit.app`

## SSL

For Option A, SSL is managed by Streamlit Community Cloud and the DNS/fronting provider. Certificate renewal is automatic.

For a self-hosted Docker/nginx deployment, use Let's Encrypt with `certbot` and auto-renew through the system timer.

## Deploy Flow

Option A:

1. Push this repository to GitHub.
2. Create a Streamlit Community Cloud app from the GitHub repo.
3. Select `app.py` as the entry point.
4. Verify the generated `*.streamlit.app` URL.
5. Add `c3twin.fledausa.com` CNAME to the Streamlit hostname if custom-domain support is available for the account, or place the Streamlit URL behind the chosen DNS/proxy setup.

Option C, Docker/nginx:

1. Build the Docker image.
2. Run the container on the host with port `8501` exposed only locally.
3. Configure nginx reverse proxy for `c3twin.fledausa.com`.
4. Issue a Let's Encrypt certificate.
5. Reload nginx and verify HTTPS.

## Rollback

Option A:

1. Revert the GitHub repository to the previous known-good commit.
2. Let Streamlit redeploy from that commit.
3. If necessary, temporarily point DNS back to the previous Streamlit hostname.

Option C:

1. Keep the previous Docker image tag.
2. Stop the current container.
3. Start the previous image tag.
4. Reload nginx only if upstream port or host changed.

## Monitoring

Minimum public-demo monitoring:

- Uptime monitor for `https://c3twin.fledausa.com`
- Health URL for Docker deployments: `/_stcore/health`
- Manual smoke test after each deploy:
  - Page loads in under 5 seconds
  - Six Plotly panels render
  - Sidebar sliders respond
  - Reset to healthy button is visible
  - Validate against experiments completes

## Open Infrastructure Questions

Before production deployment, confirm:

- What stack currently powers `fledausa.com`?
- Is Cloudflare, nginx, or another reverse proxy already in front?
- Is DNS managed through Cloudflare, Route53, the registrar, or another provider?
- Is there an existing VPS/Docker host/Kubernetes cluster?
- Should the first public demo use Streamlit Community Cloud, Hugging Face Spaces, Render/Fly, or a Fleda-controlled VPS?
