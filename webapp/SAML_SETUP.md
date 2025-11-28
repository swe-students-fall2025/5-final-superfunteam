# NYU Shibboleth/SAML Authentication Setup

This application uses NYU's Shibboleth Identity Provider for Single Sign-On (SSO) authentication.

## Prerequisites

1. **Register your application with NYU IT**
   - Contact NYU IT Services to register your app as a Service Provider (SP)
   - Provide your application's metadata URL: `https://your-app-domain.com/saml/metadata`
   - Request the NYU Shibboleth IdP certificate

2. **Obtain NYU Shibboleth Certificate**
   - Get the x509 certificate from NYU IT
   - You'll need this for `saml/settings.json`

## Configuration

### 1. Update `saml/settings.json`

Replace the following placeholders:

```json
{
    "sp": {
        "entityId": "https://YOUR-ACTUAL-DOMAIN.com/saml/metadata",
        "assertionConsumerService": {
            "url": "https://YOUR-ACTUAL-DOMAIN.com/saml/acs"
        },
        "singleLogoutService": {
            "url": "https://YOUR-ACTUAL-DOMAIN.com/saml/sls"
        }
    },
    "idp": {
        "x509cert": "PASTE_NYU_CERTIFICATE_HERE"
    }
}
```

### 2. Generate SP Certificates (Optional but Recommended)

For production, generate your own Service Provider certificates:

```bash
cd webapp/saml/certs
openssl req -new -x509 -days 3652 -nodes -out sp.crt -keyout sp.key
```

Then update `saml/settings.json`:
```json
{
    "sp": {
        "x509cert": "contents of sp.crt",
        "privateKey": "contents of sp.key"
    }
}
```

### 3. Environment Variables

Add to `.env`:
```bash
SAML_STRICT=true
SAML_DEBUG=false
SECRET_KEY=your-secure-secret-key-for-sessions
```

## NYU Shibboleth Attributes

After successful authentication, the following attributes are available:

- `urn:oid:0.9.2342.19200300.100.1.1` - NetID (username)
- `urn:oid:2.5.4.42` - First Name (givenName)
- `urn:oid:2.5.4.4` - Last Name (sn)
- `urn:oid:0.9.2342.19200300.100.1.3` - Email
- `urn:oid:1.3.6.1.4.1.5923.1.1.1.1` - Affiliation (student, faculty, staff)

The application maps these to a user session.

## Testing Authentication

### Development (Local)

For local development without NYU Shibboleth access:
1. Set `DEVELOPMENT_MODE=true` in `.env`
2. Use the mock login route: `/dev-login`
3. This bypasses SAML and creates a test session

### Production

1. Navigate to your app: `https://your-app-domain.com`
2. Click "Login with NYU NetID"
3. Redirected to NYU Shibboleth login
4. Enter NYU NetID and password
5. Redirected back to app with authenticated session

## Metadata

Your Service Provider metadata is available at:
```
https://your-app-domain.com/saml/metadata
```

Provide this URL to NYU IT when registering your application.

## Logout

Users can logout via:
- UI: Click "Logout" button
- Direct: Navigate to `/logout`
- SAML SLO: Full Single Logout from NYU Shibboleth

## Troubleshooting

### "Invalid SAML Response"
- Check that NYU certificate is correctly pasted in settings.json
- Verify URLs match your actual domain (no localhost in production)

### "User not authenticated"
- Check session configuration in app.py
- Verify SECRET_KEY is set in environment

### "Metadata not found"
- Ensure saml/settings.json is properly formatted
- Check file permissions

## Contact

For NYU Shibboleth issues:
- Email: identity-team@nyu.edu
- Documentation: https://www.nyu.edu/life/information-technology/infrastructure/identity-and-access-management.html

For application issues:
- Check application logs
- Review SAML response in browser developer tools
