# Instructions for Creating a NEW Autotask API User

**IMPORTANT: Follow these steps EXACTLY in order!**

## Step 1: Start Creating New Resource
1. Log into Autotask
2. Go to: **Admin → Resources → New**
3. **STOP! Before filling anything else...**

## Step 2: Set License Type FIRST
**This is the most critical step!**
1. In the **License Type** dropdown
2. Select: **"API User (system)"**
3. ⚠️ **NOT** "Full User" or anything else!
4. ⚠️ If you don't see "API User (system)", you need to enable API access for your account

## Step 3: Fill Required Fields
- **First Name:** API
- **Last Name:** User (or something descriptive like "PyAutotask")
- **Email:** Use a real, monitored email (for lockout notifications)
- **Username:** Make it descriptive like `api.pyautotask@yourdomain.com`
- **Status:** Active

## Step 4: Security Tab
1. Click the **Security** tab
2. **Security Level:** Select "API User (API-only)"
3. ⚠️ **NOT** "Full Access" or any other level

## Step 5: API Tracking
1. Find the **API Tracking** section (might be on General or Security tab)
2. **API Tracking Identifier:** Generate a new one or enter a custom value
3. **SAVE THIS VALUE** - This is your Integration Code

## Step 6: Generate Password
1. **Generate API User Key** or set a password
2. **SAVE THIS VALUE** - This is your Secret
3. Avoid special characters that might cause issues: `$`, `#`, `\`, quotes

## Step 7: Save and Test
1. Click **Save**
2. **Wait 5 minutes** for the user to activate
3. Test with this command:

```bash
# Replace with your values
USERNAME="your.api.user@domain.com"
SECRET="your_password_here"
INTEGRATION_CODE="your_integration_code"

# Test zone detection (should work immediately)
curl -u "${USERNAME}:${SECRET}" \
  -H "ApiIntegrationCode: ${INTEGRATION_CODE}" \
  "https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user=${USERNAME}"

# Test API access (should work after 5 minutes)
curl -u "${USERNAME}:${SECRET}" \
  -H "ApiIntegrationCode: ${INTEGRATION_CODE}" \
  -H "Content-Type: application/json" \
  -d '{"maxRecords": 1}' \
  "https://webservices14.autotask.net/ATServicesRest/v1.0/Companies/query"
```

## Common Mistakes That Cause 401 Errors

❌ **Creating a regular user first, then trying to change it to API user**
- You often CAN'T convert a regular user to API user
- Create as API User from the start

❌ **Using "Full Access" security level instead of "API User (API-only)"**
- These are different and API requires the specific API-only level

❌ **Not setting the API Tracking Identifier**
- This field is REQUIRED for REST API

❌ **Using the wrong Integration Code value**
- The Integration Code in your app must EXACTLY match the API Tracking Identifier

## What Success Looks Like

✅ Zone detection returns: 200 OK with zone info
✅ API calls return: 200 OK with data
✅ Both use the SAME credentials

## If It Still Doesn't Work

1. Double-check the License Type is "API User (system)"
2. Verify the Security Level is "API User (API-only)"
3. Ensure the API Tracking Identifier matches your Integration Code
4. Try creating a completely NEW user (don't modify existing)
5. Contact Autotask support - there may be an account-level restriction

## Quick Test Script

Save this as `test_new_user.sh`:

```bash
#!/bin/bash
echo "Enter API Username:"
read USERNAME
echo "Enter API Secret:"
read -s SECRET
echo
echo "Enter Integration Code:"
read INTEGRATION_CODE

echo "Testing zone detection..."
ZONE_RESPONSE=$(curl -s -w "\nSTATUS:%{http_code}" \
  -u "${USERNAME}:${SECRET}" \
  -H "ApiIntegrationCode: ${INTEGRATION_CODE}" \
  "https://webservices.autotask.net/atservicesrest/v1.0/zoneInformation?user=${USERNAME}")

if [[ $ZONE_RESPONSE == *"STATUS:200"* ]]; then
  echo "✅ Zone detection works!"
  ZONE_URL=$(echo "$ZONE_RESPONSE" | grep -o '"url":"[^"]*' | cut -d'"' -f4)
  echo "Zone URL: $ZONE_URL"
  
  echo "Testing API access..."
  API_STATUS=$(curl -s -w "%{http_code}" -o /dev/null \
    -u "${USERNAME}:${SECRET}" \
    -H "ApiIntegrationCode: ${INTEGRATION_CODE}" \
    -H "Content-Type: application/json" \
    -d '{"maxRecords": 1}' \
    "${ZONE_URL}v1.0/Companies/query")
  
  if [ "$API_STATUS" = "200" ]; then
    echo "✅ API access works! User is properly configured."
  else
    echo "❌ API access failed (Status: $API_STATUS)"
    echo "User is NOT configured as API User (system)"
  fi
else
  echo "❌ Zone detection failed. Check credentials."
fi
```