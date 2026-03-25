from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
import base64

from core.models import FirmaInstitucional
from .forms import FirmaInstitucionalForm
from .views import _log_audit

def _is_superadmin(user):
    """Check if user is a superadmin."""
    return user.is_authenticated and user.rol == 'superadmin'

@login_required
@user_passes_test(_is_superadmin)
def firma_list(request):
    """List all global institutional signatures."""
    firmas = FirmaInstitucional.objects.all().order_by('nombre')
    return render(request, 'panel/firmas/list.html', {'firmas': firmas})

@login_required
@user_passes_test(_is_superadmin)
def firma_create(request):
    """Create a new institutional signature."""
    if request.method == 'POST':
        form = FirmaInstitucionalForm(request.POST)
        if form.is_valid():
            firma = form.save(commit=False)
            if 'imagen' in request.FILES:
                file_obj = request.FILES['imagen']
                encoded = base64.b64encode(file_obj.read()).decode('utf-8')
                firma.imagen = encoded
            firma.save()
            _log_audit(request.user, 'CREAR_FIRMA', f'Firma Institucional creada: {firma.nombre}')
            messages.success(request, 'Firma institucional creada correctamente.')
            return redirect('panel:firma_list')
    else:
        form = FirmaInstitucionalForm()
    return render(request, 'panel/firmas/form.html', {'form': form, 'title': 'Nueva Firma Institucional'})

@login_required
@user_passes_test(_is_superadmin)
def firma_edit(request, id):
    """Edit an existing institutional signature."""
    firma = get_object_or_404(FirmaInstitucional, id=id)
    if request.method == 'POST':
        form = FirmaInstitucionalForm(request.POST, instance=firma)
        if form.is_valid():
            firma_obj = form.save(commit=False)
            if 'imagen' in request.FILES:
                file_obj = request.FILES['imagen']
                encoded = base64.b64encode(file_obj.read()).decode('utf-8')
                firma_obj.imagen = encoded
            firma_obj.save()
            _log_audit(request.user, 'EDITAR_FIRMA', f'Firma Institucional editada: {firma_obj.nombre}')
            messages.success(request, 'Firma institucional actualizada correctamente.')
            return redirect('panel:firma_list')
    else:
        form = FirmaInstitucionalForm(instance=firma)
    return render(request, 'panel/firmas/form.html', {'form': form, 'firma': firma, 'title': 'Editar Firma Institucional'})

@login_required
@user_passes_test(_is_superadmin)
def firma_delete(request, id):
    """Delete an institutional signature."""
    firma = get_object_or_404(FirmaInstitucional, id=id)
    if request.method == 'POST':
        nombre = firma.nombre
        firma.delete()
        _log_audit(request.user, 'ELIMINAR_FIRMA', f'Firma Institucional eliminada: {nombre}')
        messages.success(request, f'Firma "{nombre}" eliminada correctamente.')
    return redirect('panel:firma_list')
