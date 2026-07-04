import time
from celery import shared_task
from .models import Report
from core.thread_local import set_current_tenant, get_current_tenant, clear_thread_local

@shared_task
def generate_report_task(tenant_id, report_id):
    set_current_tenant(tenant_id)
    
    try:
        report = Report.objects.get(id=report_id) # ini otomatis filter (tenant_id=tenant_id) karena Report pake StrictTenantManager, pake report_id biar sesuai report_id yang mana
        
        # ubah status ke GENERATING
        report.status = Report.Status.GENERATING
        report.save() # simpen perubahan ke database
        
        # simulasi bikin berat 
        time.sleep(30)
        
        # kalo berhasil, kasih URL dan ubah status
        report.file_url = "https://s3.aws.com/warkop-saas/laporan_dummy.pdf"
        report.status = Report.Status.SUCCESS
        report.save()
        
    except Exception as e:
        # kalo gagal (server ngelag, bug, etc), ubah status jadi failed
        report = Report.objects.filter(id=report_id).first()
        if report:
            report.status = Report.Status.FAILED
            report.save()
        print(f"Error Celery: {e}")
    finally:
        clear_thread_local()
        
        