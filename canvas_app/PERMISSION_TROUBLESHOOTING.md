# Canvas API Permission Troubleshooting Guide

This guide helps you diagnose and resolve Canvas API permission issues that prevent access to course files and other data.

## 🚨 Common Permission Errors

### "Access forbidden - insufficient permissions"
This error occurs when your Canvas API token doesn't have the necessary permissions to access the requested resource.

### "Files access forbidden"
Your API token lacks permission to access course files. This is common for student accounts.

### "Authentication failed"
Your API token is invalid, expired, or the Canvas URL is incorrect.

## 🔧 Diagnostic Tools

### 1. Permission Diagnostic Tool
```bash
python canvas_permission_diagnostic.py <canvas_url> <api_token> [course_id]
```

**Example:**
```bash
python canvas_permission_diagnostic.py https://your-school.instructure.com your_token_here 12345
```

### 2. Interactive Diagnostic Runner
```bash
python run_permission_diagnostic.py
```

This will prompt you for your Canvas URL, API token, and optional course ID.

### 3. Permission Validator
```bash
python canvas_permission_validator.py <canvas_url> <api_token> [course_id]
```

## 📋 Step-by-Step Solutions

### For Files Access Issues:

1. **Check Your API Token Permissions:**
   - Go to Canvas → Account → Settings → Approved Integrations
   - Find your existing token or create a new one
   - Ensure the token has the following scopes:
     - `/auth/userinfo` (User information)
     - `/auth/canvas` (Canvas API access)
     - `/auth/canvas/files` (File access) ⭐ **This is crucial for files**
     - `/auth/canvas/courses` (Course access)

2. **Verify Course Access:**
   - Make sure you're enrolled in the course
   - Check if the course has files available
   - Verify you have the right role (student, teacher, etc.)

3. **Contact Your Administrator:**
   - If you cannot modify token scopes, contact your Canvas administrator
   - Request elevated permissions for file access
   - Some institutions restrict file access via API for students

### For Authentication Issues:

1. **Generate a New API Token:**
   - Go to Canvas → Account → Settings → Approved Integrations
   - Delete the old token
   - Create a new token with all necessary scopes
   - Copy the token immediately (it won't be shown again)

2. **Verify Canvas URL:**
   - Ensure the URL is correct (e.g., `https://your-school.instructure.com`)
   - Don't include `/api/v1` in the base URL
   - Check for typos in the URL

3. **Test the Token:**
   - Use the diagnostic tools to verify the token works
   - Check if the token is copied correctly (no extra spaces, etc.)

## 🎯 Understanding Permission Levels

### Student Account:
- ✅ Can access: User profile, enrolled courses, assignments, modules
- ❌ May not access: Course files, other users' data, grades
- 💡 **Solution:** Use Canvas web interface for file downloads

### Teacher/Instructor Account:
- ✅ Can access: All course data including files
- ✅ Can access: Student information, grades, submissions
- 💡 **Solution:** Ensure token has all necessary scopes

### Administrator Account:
- ✅ Can access: All institutional data
- ✅ Can access: All courses and users
- 💡 **Solution:** Token should have full permissions

## 🔍 Diagnostic Output Interpretation

### ✅ Success Indicators:
- "Authentication successful"
- "Files access successful: X files found"
- "All tests passed! Your Canvas API token has the necessary permissions."

### ❌ Error Indicators:
- "Authentication failed: 401"
- "Files access forbidden - insufficient permissions"
- "Access forbidden - insufficient permissions"

### ⚠️ Warning Indicators:
- "Files access failed: 403" (Permission denied)
- "Courses access failed: 404" (Not found or no access)

## 🛠️ Alternative Solutions

### If API Access is Restricted:

1. **Manual File Downloads:**
   - Use the Canvas web interface
   - Download files individually or in bulk
   - Use browser extensions for batch downloads

2. **Canvas Mobile App:**
   - Download files through the mobile app
   - Sync to cloud storage services

3. **Instructor Assistance:**
   - Ask instructors to share files via email
   - Request file access through course announcements

### If You Need Programmatic Access:

1. **Request Elevated Permissions:**
   - Contact your Canvas administrator
   - Explain your use case for API access
   - Request specific scopes needed

2. **Use Canvas Export Features:**
   - Export course content as ZIP files
   - Use Canvas's built-in export tools
   - Download course packages

## 📞 Getting Help

### Canvas Support:
- Check Canvas documentation: https://canvas.instructure.com/doc/api/
- Contact your institution's Canvas support team
- Use Canvas community forums

### Technical Support:
- Run the diagnostic tools and save the reports
- Include the diagnostic output when requesting help
- Provide your Canvas URL and error messages

## 🔄 Regular Maintenance

### Token Management:
- Regenerate tokens periodically for security
- Monitor token usage and permissions
- Keep track of which applications use which tokens

### Permission Audits:
- Run diagnostic tools monthly
- Check for new permission requirements
- Update tokens when course access changes

## 📊 Diagnostic Reports

The diagnostic tools generate detailed reports that include:
- Authentication status
- Permission levels for each API endpoint
- Specific error messages and codes
- Recommended solutions
- Troubleshooting steps

Save these reports for reference and when requesting technical support.

---

**Need more help?** Run the diagnostic tools and check the generated reports for specific guidance based on your Canvas setup and permissions.
