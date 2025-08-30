# Autotask API User Setup Checklist

## Required Configuration for API Users

When creating an API user in Autotask, ALL of the following must be configured correctly:

### 1. User Type & License
- [ ] **License Type**: Must be "API User (system)" - NOT a regular user license
- [ ] **Security Level**: Must be "API User (API-only)" - NOT "Full Access" or any other level
- [ ] This is a special license type that:
  - Does NOT count against your user licenses
  - Does NOT allow UI login
  - ONLY allows API access

### 2. Required Fields
- [ ] **Username**: Must be in email format (e.g., api@yourdomain.com)
- [ ] **Email Address**: Should be a real, monitored email (for lockout notifications)
- [ ] **First Name**: Required field (can be "API")
- [ ] **Last Name**: Required field (can be "User")
- [ ] **Status**: Must be "Active"

### 3. API-Specific Settings
- [ ] **API Tracking Identifier**: MUST be set (this is critical!)
  - Find this in: Admin → Resources → Edit Resource → API Tracking section
  - This is your Integration Code
- [ ] **Generate API User Key**: Must be generated and saved
  - This becomes your secret/password
- [ ] **Integration Code**: Must match what you're using in the API calls

### 4. Security Level Assignment
Navigate to: Admin → Resources → Security Levels
- [ ] Ensure "API User (API-only)" security level exists
- [ ] Assign this security level to your API user
- [ ] Do NOT assign any regular user security levels

### 5. Common Issues That Cause 401 Errors

1. **Wrong License Type**: Using a regular user license instead of API User (system)
2. **Wrong Security Level**: Using "Full Access" instead of "API User (API-only)"
3. **Missing API Tracking Identifier**: This field is required for REST API
4. **User Not Active**: Check the user's status
5. **Integration Code Mismatch**: The code in your app must match exactly
6. **Recently Created**: Wait 5 minutes after creation for activation

### 6. How to Verify in Autotask UI

1. Go to: **Admin → Resources**
2. Find your API user
3. Click Edit
4. Check the **General** tab:
   - Verify License Type = "API User (system)"
   - Verify Status = "Active"
5. Check the **Security** tab:
   - Verify Security Level = "API User (API-only)"
6. Check the **API Tracking** section:
   - Verify API Tracking Identifier is set
   - This should match your Integration Code

### 7. Testing Your Configuration

Your zone detection works (✅), which means:
- Your username is valid
- Your secret/password is correct
- Your integration code format is correct

But API calls fail (❌), which typically means:
- Wrong license type (not API User)
- Wrong security level (not API-only)
- Missing API tracking identifier
- User is inactive

### 8. If Everything Above Is Correct

If you've verified all the above and it still doesn't work:
1. Try creating a brand new API user from scratch
2. Make sure to select "API User (system)" license type DURING creation
3. Contact Autotask support - there may be an account-level issue

## Key Insight

The fact that zone detection works but API calls fail is the classic symptom of:
- Using a regular user account with an API integration code
- Instead of a proper API User (system) account

Regular users can do zone detection but cannot make API calls, even with an integration code.