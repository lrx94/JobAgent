# Streamlit Community Cloud deployment

## Application configuration

- Repository: `lrx94/JobAgent`
- Branch: choose the branch approved for production.
- Entrypoint: `app.py`
- Python: use a Streamlit-supported version compatible with the project.
- Python dependencies: `requirements.txt` at the repository root.

Community Cloud executes the application from the repository root. JobAgent's
relative paths (`profiles/`, `data/`, and `data/users/`) are therefore portable.
The Workspace creates each authorized user's directories on first use.

Community Cloud's local filesystem is not durable application storage. A reboot,
redeployment, or platform maintenance can remove uploaded CVs, profiles, learning
state, and SQLite data. Durable production storage is a separate follow-up.

## Google OIDC

Create a Google OAuth web client and register this exact authorized redirect URI:

```text
https://VOTRE-APP.streamlit.app/oauth2callback
```

The same URI must be configured as `auth.redirect_uri` in Streamlit secrets. If
the app subdomain changes, update both Google OAuth and Streamlit secrets.

## Streamlit secrets

Open the app's **Settings > Secrets** and copy the structure from
`.streamlit/secrets.example.toml`, replacing placeholders in the Cloud console.
Never commit `.streamlit/secrets.toml`.

Mandatory for authentication and authorization:

- `auth.redirect_uri`
- `auth.cookie_secret`
- `auth.client_id`
- `auth.client_secret`
- `auth.server_metadata_url`
- `access.allowed_emails`

Optional, depending on enabled features:

- `OPENAI_API_KEY`
- `FRANCE_TRAVAIL_CLIENT_ID`
- `FRANCE_TRAVAIL_CLIENT_SECRET`
- `FRANCE_TRAVAIL_TOKEN_URL`
- `FRANCE_TRAVAIL_SEARCH_URL`
- `FRANCE_TRAVAIL_SCOPE`
- `FRANCE_TRAVAIL_TIMEOUT`
- `FRANCE_TRAVAIL_USER_AGENT`

RemoteOK does not require a secret.

## Allow an external user

1. Open the deployed app in Streamlit Community Cloud.
2. Select **Manage app**, then **Settings > Secrets**.
3. Add the Google account email to `access.allowed_emails`:

   ```toml
   [access]
   allowed_emails = [
       "first-user@example.com",
       "new-user@example.com",
   ]
   ```

4. Save the secrets and let Streamlit restart the app if requested.
5. Ask the user to sign in with the same verified Google email.

Email comparison ignores surrounding whitespace and character case. If the
`[access]` section or `allowed_emails` is missing, JobAgent fails closed and does
not grant access.

## Publication steps

1. Push the approved branch to GitHub.
2. Go to `https://share.streamlit.io` and select **Create app**.
3. Select the repository, approved branch, and `app.py` entrypoint.
4. Choose the final app subdomain.
5. Open **Advanced settings**, select a compatible Python version, and paste the
   secrets without exposing their values in Git.
6. Deploy and inspect the build logs.
7. Validate anonymous, authorized, and unauthorized login flows.
8. Open the Career Workspace and verify that its user-specific directories can
   be created.

Official references:

- <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy>
- <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management>
- <https://docs.streamlit.io/develop/concepts/connections/authentication>
