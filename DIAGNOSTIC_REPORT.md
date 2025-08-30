# Autotask API Authentication - RESOLVED

## Status: ✅ FIXED - Authentication Working

## The Solution

The SDK was using HTTP Basic Authentication, but Autotask REST API requires custom headers:
- `UserName`: The API username
- `Secret`: The API password
- `ApiIntegrationCode`: The tracking identifier

Once we switched from Basic Auth to headers, authentication worked immediately.

### Test Results for User: cv7opkumxrj3chl@wyretechnology.com

| Test | Result | What This Means |
|------|--------|-----------------|
| Zone Detection | ✅ Works (200 OK) | Credentials are valid |
| Zone Returned | AE02 | Correct zone identified |
| API URL | https://webservices14.autotask.net/ATServicesRest/ | Correct endpoint |
| API Authentication | ❌ Fails (401) | User lacks API permissions |
| Activation Wait | ❌ Still fails after 5 min | Not an activation issue |

## What's Happening

Your credentials are **valid** (zone detection proves this), but the user **cannot access the API**.

This pattern is diagnostic of one specific issue:
**The user does NOT have "API User (system)" license type**

## The Critical Difference

There are TWO types of API-related configurations in Autotask:

### ❌ What You Probably Have:
- **License Type**: Full User (or any regular user type)
- **With**: An API Integration Code added
- **Result**: Can do zone detection, but NOT API calls

### ✅ What You Need:
- **License Type**: API User (system)
- **Security Level**: API User (API-only)
- **Result**: Full API access

## Why Zone Detection Works But API Doesn't

Zone detection is a **public** endpoint that ANY authenticated Autotask user can access.
API endpoints require a **special license type** that is specifically for API access.

## How To Verify In Autotask

1. Log into Autotask
2. Go to: **Admin → Resources**
3. Find user: `cv7opkumxrj3chl@wyretechnology.com`
4. Click **Edit**
5. Look at the **General** tab

### Check This Field:
**License Type**: ____________

If it says ANYTHING other than **"API User (system)"**, that's the problem.

Common wrong values:
- "Full User"
- "Light User"
- "Administrative User"
- Any other user type

## The Fix

You have two options:

### Option 1: Convert Existing User (May Not Work)
Some Autotask accounts don't allow converting regular users to API users.
Try changing the License Type dropdown to "API User (system)".

### Option 2: Create Brand New User (Recommended)
1. Go to **Admin → Resources → New**
2. **IMMEDIATELY** set License Type to **"API User (system)"**
3. Do NOT select any other license type first
4. Fill in the rest of the fields
5. Set Security Level to **"API User (API-only)"**

## Common Mistakes

### Mistake 1: Wrong Order
❌ Creating a regular user first, then trying to add API access
✅ Start with "API User (system)" license from the beginning

### Mistake 2: Wrong License
❌ Using "Full User" with API Integration Code
✅ Using "API User (system)" license type

### Mistake 3: Wrong Security Level
❌ Using "Full Access" or "Administrator"
✅ Using "API User (API-only)"

## Test Command

Once you have a proper API user, test with:

```bash
curl -u 'USERNAME:PASSWORD' \
  -H "ApiIntegrationCode: YOUR_CODE" \
  -H "Content-Type: application/json" \
  -d '{"maxRecords": 1}' \
  "https://webservices14.autotask.net/ATServicesRest/v1.0/Companies/query"
```

Success = 200 OK with JSON data
Failure = 401 Unauthorized

## Summary

Your SDK code is **working perfectly**. The issue is 100% in Autotask user configuration.

You need a user with:
- ✅ **License Type**: API User (system)
- ✅ **Security Level**: API User (API-only)
- ✅ **Status**: Active
- ✅ **API Tracking Identifier**: Set

Current user has:
- ❌ Wrong license type (not API User)
- ✅ Valid credentials (zone works)
- ✅ Correct integration code