import structlog
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.utils.text import slugify
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from tenants.models import Organization, Membership
from documents.models import Document
from search.models import QueryLog
from django_ratelimit.decorators import ratelimit
from audit.services import log_action
from documents.utils import sanitize_text

logger = structlog.get_logger(__name__)

@ratelimit(key='ip', rate='5/m', block=False)
def login_view(request):
    if getattr(request, 'limited', False):
        return render(request, 'auth/login.html', {'error': 'Too many login attempts. Please try again in a minute.'})
    if request.user.is_authenticated:
        # Only redirect if user has an org, otherwise let them see login page
        has_org = Membership.objects.filter(user=request.user, is_active=True).exists()
        if has_org:
            return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                # Log successful login
                membership = Membership.objects.filter(user=user, is_active=True).first()
                org = membership.organization if membership else None
                log_action(user, org, 'USER_LOGGED_IN', request)
                return redirect('dashboard')
            else:
                return render(request, 'auth/login.html', {'error': 'Invalid credentials.'})
        except User.DoesNotExist:
            return render(request, 'auth/login.html', {'error': 'No account with this email.'})
    return render(request, 'auth/login.html')

@ratelimit(key='ip', rate='5/m', block=False)
def register_view(request):
    if getattr(request, 'limited', False):
        return render(request, 'auth/register.html', {'error': 'Too many registration attempts. Please try again later.'})
    if request.user.is_authenticated:
        # Only redirect if user already has an org — prevents redirect loop
        has_org = Membership.objects.filter(user=request.user, is_active=True).exists()
        if has_org:
            return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        org_name = request.POST.get('org_name')

        if User.objects.filter(email=email).exists():
            return render(request, 'auth/register.html', {'error': 'Email already registered.'})

        user = User.objects.create_user(
            email=email, username=username, password=password
        )
        slug = slugify(org_name)
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Organization.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization.objects.create(name=org_name, slug=slug)
        Membership.objects.create(user=user, organization=org, role=Membership.Role.OWNER)
        
        # Log successful registration
        log_action(user, org, 'USER_REGISTERED', request, payload={'email': email, 'org_name': org_name})
        
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('dashboard')

    return render(request, 'auth/register.html')


def logout_view(request):
    logout(request)
    return redirect('login_view')


def get_user_org(request):
    """Get the first active organization for the logged-in user."""
    membership = Membership.objects.filter(
        user=request.user, is_active=True
    ).select_related('organization').first()
    return membership.organization if membership else None


@login_required
def dashboard(request):
    org = get_user_org(request)
    if not org:
        # Log out the orphan user and send to register — prevents redirect loop
        logout(request)
        return redirect('register_view')

    from django.utils import timezone
    from datetime import timedelta
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)

    documents = Document.objects.filter(organization=org).order_by('-created_at')[:10]
    total_queries = QueryLog.objects.filter(
        organization=org,
        created_at__gte=month_start
    ).count()

    return render(request, 'dashboard/dashboard.html', {
        'org_name': org.name,
        'total_documents': Document.objects.filter(organization=org).count(),
        'ready_documents': Document.objects.filter(organization=org, status='READY').count(),
        'total_queries': total_queries,
        'documents': documents,
    })


@login_required
def upload_view(request):
    org = get_user_org(request)
    return render(request, 'dashboard/upload.html', {
        'org_id': str(org.id) if org else '',
    })


@login_required
def chat_view(request):
    org = get_user_org(request)
    refresh = RefreshToken.for_user(request.user)
    return render(request, 'dashboard/chat.html', {
        'org_id': str(org.id),
        'access_token': str(refresh.access_token),
    })


@login_required
@require_http_methods(["POST"])
@ratelimit(key='ip', rate='10/m', block=False)
def upload_document(request):
    if getattr(request, 'limited', False):
        return HttpResponse('<div class="alert alert-error">Rate limit exceeded. Please wait a minute before uploading again.</div>')
    from documents.models import Document
    from documents.tasks import ingest_document

    org = get_user_org(request)
    file = request.FILES.get('file')
    # Sanitize the title with bleach to prevent stored XSS
    raw_title = request.POST.get('title', file.name if file else 'Untitled')
    title = sanitize_text(raw_title)

    if not file:
        return HttpResponse('<div class="alert alert-error">No file provided.</div>')

    ext = file.name.split('.')[-1].upper()
    if ext not in ['PDF', 'DOCX', 'TXT']:
        return HttpResponse('<div class="alert alert-error">Unsupported file type.</div>')

    if file.size > 20 * 1024 * 1024:
        return HttpResponse('<div class="alert alert-error">File too large. Max 20MB.</div>')

    document = Document.objects.create(
        organization=org,
        uploaded_by=request.user,
        title=title,
        file=file,
        file_type=ext,
        file_size=file.size,
        status=Document.Status.PENDING
    )
    
    # Log the document upload
    log_action(
        request.user, 
        org, 
        'DOCUMENT_UPLOADED', 
        request, 
        payload={'document_id': str(document.id), 'title': title, 'size': file.size}
    )
    
    ingest_document.delay(str(document.id))

    return HttpResponse(f'<div class="alert alert-success">✓ "{title}" uploaded. Processing started.</div>')


@login_required
def document_list_partial(request):
    org = get_user_org(request)
    documents = Document.objects.filter(organization=org).order_by('-created_at')
    return render(request, 'dashboard/document_list_partial.html', {'documents': documents})

# Create your views here.
