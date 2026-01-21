# Django Backend Code Analysis Report
**Generated**: January 21, 2026
**Project**: Website Backend API

---

## ✅ PASSING TESTS

### 1. System & Configuration
- ✓ Django system check: **0 issues**
- ✓ All migrations applied successfully (37 applied across all apps)
- ✓ Python 3.13.0 environment properly configured
- ✓ Virtual environment active and functional

### 2. Database Connectivity
- ✓ **PostgreSQL**: Connected successfully
  - Staff count: 3
  - All models accessible
  - Database operations functional
  
- ✓ **MongoDB (CosmosDB)**: Connected successfully
  - Messages collection: 197 documents
  - CRUD operations functional
  - NOTE: CosmosDB cluster detected (warnings are normal)

### 3. Code Quality
- ✓ No syntax errors detected in any Python files
- ✓ All required imports available
- ✓ No circular dependencies
- ✓ All views and serializers importing correctly

### 4. Data Distribution
- Staff Workload Analysis:
  - Manager: 0 items (inactive)
  - Two: 51 items (27 students + 24 enquiries)
  - Rintu Sam: 51 items (28 students + 23 enquiries)
  - **Status**: Balanced distribution ✓

---

## ⚠️ ISSUES IDENTIFIED

### 1. **Orphaned Data Issues**
- **Orphaned Enquiries**: 1 record found
  - This enquiry has `assigned_staff = NULL`
  - Likely from deleted staff member or import error
  - **Action Required**: Review and reassign or delete

### 2. **Dead/Debug Code - 19 Files Found**
The following test/debug files are cluttering the root directory. Determine if still needed:

#### Development/Testing Scripts (likely safe to remove):
- `test_allocation.py` - Tests staff allocation logic
- `test_chat.py` - Tests chat functionality
- `test_messages.py` - Tests MongoDB message queries
- `test_query.py` - Tests database queries
- `debug_api.py` - API testing script
- `debug_api_null.py` - Tests null handling
- `debug_users.py` - Lists staff users
- `check_admin_fix.py` - Admin creation verification
- `check_image_size.py` - Image size check
- `check_messages.py` - Message statistics
- `check_password.py` - Password verification

#### Maintenance Scripts (review for active use):
- `cleanup_duplicates.py` - Removes duplicate entries (should be in management commands)
- `cleanup_orphaned_data.py` - Cleans orphaned records (should be in management commands)
- `diagnose_orphaned_data.py` - Diagnostic tool (should be in management commands)
- `verify_email_unique.py` - Email uniqueness check
- `verify_fix.py` - General verification
- `verify_mongo.py` - MongoDB verification
- `reproduce_error.py` - Error reproduction
- `reproduce_image_upload.py` - Image upload testing

### 3. **Commented Out Code**
**Location**: `chat/models.py` (lines 3-23)
```python
# class Message(models.Model):
#     # ...entire model commented out...
```
- Old Django ORM message model, replaced by MongoDB
- Using MongoDB mongo_client.py instead
- **Action**: Remove commented code (cleanup complete migration to MongoDB)

### 4. **Missing `requests` Package**
- **Issue**: `requests` library used in 4 test files but not in requirements.txt
- **Affected files**:
  - test_allocation.py
  - debug_api.py
  - debug_api_null.py
  - reproduce_image_upload.py
- **Impact**: Tests cannot run without installation
- **Recommendation**: Either add to requirements.txt OR move these files to separate test directory

### 5. **Security Issues**

#### a) Hardcoded Credentials in settings.py
```python
SECRET_KEY = 'django-insecure-by#83o71q!g7@19^ow+jxevm0ee343$udkj25dt_bun@z9qy+d'
MONGO_URI = "mongodb+srv://laren:%40password123@somerandommongodbdatabase..."
```
- **Risk Level**: **HIGH**
- **Action Required**: 
  - Move to environment variables
  - Use `.env` file with python-dotenv
  - Never commit sensitive keys

#### b) Hardcoded Admin Bootstrap
**Location**: `formapp/views.py` (staff_login function, line ~60)
```python
if login_id == 'admin' and password == 'admin123':
    return Response({"message": "Admin Login", "role": "admin", "staff_id": None})
```
- Temporary bootstrap credentials in production code
- **Action**: Remove after setting up proper admin user

#### c) CORS Configuration
```python
CORS_ALLOW_ALL_ORIGINS = True
```
- **Risk Level**: **MEDIUM** (development-friendly, not production-safe)
- **Action**: Specify allowed origins for production

#### d) DEBUG Mode
```python
DEBUG = True
```
- **Risk Level**: **MEDIUM** (exposes stack traces)
- **Action**: Set to False in production

### 6. **Data Consistency Issues**

#### a) Plus Two Percentage (Legacy Field)
- **Location**: `formapp/models.py`, line ~130
- **Issue**: Both `aggregate_percentage` and `plus_two_percentage` fields exist
- Redundant fields - should consolidate
- One stores string, one stores decimal (inconsistent types)
- **Action**: Migrate data to single field, deprecate legacy field

#### b) Email Unique Constraint Missing
- `CollectionForm.email` - Not unique, but used for deduplication
- `Enquiry.email` - Nullable, inconsistent
- **Action**: Add proper unique constraints or handle duplicates

#### c) Phone Number Validation
- All phone fields assume 10-digit Indian numbers
- Hardcoded regex: `r'^\d{10}$'`
- **Issue**: Not flexible for international numbers
- **Action**: Consider making configurable or adding format options

### 7. **Performance Issues**

#### a) N+1 Query Problem Risk
- **Location**: `formapp/utils.py`, `allocate_staff()` function
- Loops through active staff and calls `.count()` for each
- For 100+ staff, this means 200+ database queries
- **Recommendation**: Use Django ORM annotations instead:
  ```python
  from django.db.models import Count
  staff_workloads = active_staff.annotate(
      workload=Count('assigned_students') + Count('assigned_enquiries')
  ).order_by('workload', 'id')
  ```

#### b) Missing Database Indexes
- `CollectionForm.email` has index but is not unique
- `CollectionForm.created_at` has no index (commonly filtered/sorted)
- `Enquiry.created_at` has no index
- **Action**: Add indexes for frequently filtered/sorted fields

### 8. **API URL Routing Issue**
**Location**: `formapp/urls.py`, line ~20
```python
path('staff/reallocate/', views.reallocate_leads),  # Before staff/<pk>/
path('staff/<int:pk>/', staff_detail),              # Catches '/staff/reallocate/'
```
- **Issue**: URL pattern order matters! `/staff/reallocate/` will be intercepted by `/staff/<pk>/`
- If `reallocate` is treated as `pk`, it will fail
- **Action**: Reorder URLs - specific paths before generic `<pk>` paths

### 9. **Unused/Incomplete Features**

#### a) StaffDocument Model
- Exists but no clear usage in views
- Uploaded to `staff_documents/` but no size limits
- **Recommendation**: Verify if actively used or remove

#### b) extra_data Field in CollectionForm
- JSONField for extensibility (good design)
- But frontend might not know what fields to include
- Consider documenting schema

#### c) Role-Based Access Control
- Views have `role` parameter but not enforced
- No authentication middleware enforcing staff identity
- **Recommendation**: Implement proper authentication (JWT tokens)

### 10. **Code Quality Improvements Needed**

#### a) Inconsistent Error Handling
- Some views check `DoesNotExist`, others assume existence
- Some use try/except, others don't

#### b) Magic Strings
- Hardcoded role strings: `'admin'`, `'staff'`
- Status values: `'Pending'`, `'In Progress'`, etc.
- **Recommendation**: Use enum classes

#### c) Missing Docstrings
- Many functions lack documentation
- API parameters not documented

---

## 📋 RECOMMENDATIONS & ACTION ITEMS

### Priority 1 (Critical - Fix Now)
- [ ] Move sensitive credentials to environment variables
- [ ] Fix URL routing order (reallocate before `<pk>`)
- [ ] Remove or migrate orphaned enquiry
- [ ] Fix N+1 query in `allocate_staff()`

### Priority 2 (High - Fix Soon)
- [ ] Remove hardcoded admin bootstrap credentials
- [ ] Add proper authentication/JWT tokens
- [ ] Move debug/test files to separate directory or remove
- [ ] Add `requests` to requirements.txt or remove test files
- [ ] Remove commented-out code from chat/models.py

### Priority 3 (Medium - Improve)
- [ ] Consolidate duplicate percentage fields
- [ ] Add indexes for performance
- [ ] Configure CORS for specific origins
- [ ] Add proper error handling throughout
- [ ] Use enum classes for constants
- [ ] Set DEBUG=False for production config

### Priority 4 (Low - Consider)
- [ ] Add docstrings to all functions
- [ ] Convert test files to proper Django test suite
- [ ] Document API endpoints with Swagger/OpenAPI
- [ ] Add input validation with Django validators
- [ ] Consider international phone number support

---

## 🧹 CLEANUP RECOMMENDATIONS

### Files to Review/Remove

**Safe to Remove (Debug/Test files):**
```
test_allocation.py
test_chat.py
test_messages.py
test_query.py
debug_api.py
debug_api_null.py
debug_users.py
check_admin_fix.py
check_image_size.py
check_messages.py
check_password.py
reproduce_error.py
reproduce_image_upload.py
```

**Consider Moving to `management/commands/` or Django Tests:**
```
cleanup_duplicates.py
cleanup_orphaned_data.py
diagnose_orphaned_data.py
verify_email_unique.py
verify_fix.py
verify_mongo.py
```

### Code to Remove
- Commented-out Message model in `chat/models.py`
- Hardcoded admin bootstrap in `formapp/views.py`

---

## 📊 SUMMARY

| Category | Status | Issues |
|----------|--------|--------|
| Syntax & Imports | ✅ PASS | 0 |
| Database Connectivity | ✅ PASS | 0 |
| Security | ⚠️ WARNING | 4 issues |
| Data Integrity | ⚠️ WARNING | 1 orphaned record |
| Code Quality | ⚠️ WARNING | 5 issues |
| Performance | ⚠️ WARNING | 2 issues |
| Dead Code | ⚠️ WARNING | 19 test files + commented code |

**Overall Status**: 🟡 **FUNCTIONAL BUT NEEDS CLEANUP & SECURITY FIXES**

