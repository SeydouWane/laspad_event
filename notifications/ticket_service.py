# -*- coding: utf-8 -*-
"""
Génération du ticket PDF avec QR code pour les participants en présentiel.
Utilise ReportLab (déjà installé sur le serveur).
"""
import io
import os
import qrcode
from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from django.conf import settings


# ── Couleurs LASPAD ─────────────────────────────────────────────
VERT_LASPAD = colors.HexColor('#1a6b3a')
OR_LASPAD   = colors.HexColor('#c9a227')
NOIR_LASPAD = colors.HexColor('#0f1f15')
GRIS_CLAIR  = colors.HexColor('#f8f9fa')
GRIS_BORD   = colors.HexColor('#e9ecef')


def _make_qr(data: str) -> ImageReader:
    """Génère un QR code et retourne un ImageReader ReportLab."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return ImageReader(buf)


def _logo_reader() -> ImageReader | None:
    """Charge le logo LASPAD depuis static/img/logo.png."""
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        return ImageReader(logo_path)
    return None


def generate_ticket_pdf(registration) -> bytes:
    """
    Génère le ticket PDF pour une inscription acceptée en présentiel.
    Retourne le contenu PDF en bytes.
    """
    event       = registration.event
    participant = registration.participant
    site_url    = getattr(settings, 'SITE_URL', 'https://events.laspad.org')

    # URL du QR code — pointe vers la page de scan
    qr_url  = f"{site_url}/dashboard/scan/{registration.token}/"
    qr_img  = _make_qr(qr_url)
    logo    = _logo_reader()

    buf = io.BytesIO()
    w, h = A4  # 595 x 842 pts

    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f"Ticket — {event.title}")

    # ── Fond haut (bandeau vert) ────────────────────────────────
    c.setFillColor(NOIR_LASPAD)
    c.rect(0, h - 90*mm, w, 90*mm, fill=1, stroke=0)

    # Logo
    if logo:
        c.drawImage(logo, 15*mm, h - 75*mm, width=40*mm, height=20*mm,
                    preserveAspectRatio=True, mask='auto')

    # Titre LASPAD EVENT
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(62*mm, h - 30*mm, 'LASPAD EVENT')
    c.setFont('Helvetica', 11)
    c.setFillColor(OR_LASPAD)
    c.drawString(62*mm, h - 40*mm, 'Ticket de participation')

    # Numéro de ticket (en haut à droite)
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(OR_LASPAD)
    ticket_no = registration.ticket_number or str(registration.token)[:8].upper()
    c.drawRightString(w - 15*mm, h - 25*mm, f'N° {ticket_no}')

    # ── Séparateur doré ─────────────────────────────────────────
    c.setStrokeColor(OR_LASPAD)
    c.setLineWidth(2)
    c.line(15*mm, h - 92*mm, w - 15*mm, h - 92*mm)

    # ── Titre de l'événement ────────────────────────────────────
    y = h - 108*mm
    c.setFillColor(NOIR_LASPAD)
    c.setFont('Helvetica-Bold', 16)
    # Découper le titre si trop long
    title = event.title
    if len(title) > 55:
        title = title[:52] + '...'
    c.drawString(15*mm, y, title)

    # Type d'événement
    y -= 8*mm
    c.setFont('Helvetica', 10)
    c.setFillColor(VERT_LASPAD)
    c.drawString(15*mm, y, f'[ {event.get_event_type_display().upper()} ]')

    # ── Bloc infos (fond gris clair) ────────────────────────────
    y -= 8*mm
    bloc_y = y - 52*mm
    c.setFillColor(GRIS_CLAIR)
    c.roundRect(15*mm, bloc_y, w - 30*mm, 52*mm, 3*mm, fill=1, stroke=0)
    c.setStrokeColor(GRIS_BORD)
    c.setLineWidth(0.5)
    c.roundRect(15*mm, bloc_y, w - 30*mm, 52*mm, 3*mm, fill=0, stroke=1)

    def info_row(label, value, y_pos, icon=''):
        c.setFont('Helvetica-Bold', 9)
        c.setFillColor(colors.HexColor('#6b7280'))
        c.drawString(20*mm, y_pos, f'{icon}  {label}'.strip())
        c.setFont('Helvetica', 10)
        c.setFillColor(NOIR_LASPAD)
        c.drawString(65*mm, y_pos, value)

    row_y = y - 10*mm
    # Date
    date_str = event.start_datetime.strftime('%d %B %Y à %Hh%M')
    if event.start_datetime.date() != event.end_datetime.date():
        date_str += f" — {event.end_datetime.strftime('%d %B %Y')}"
    info_row('Date', date_str, row_y, '📅')

    row_y -= 9*mm
    # Lieu
    lieu = '—'
    if event.location:
        if event.location.mode == 'online':
            lieu = 'En ligne'
        elif event.location.city:
            lieu = f"{event.location.address or ''} {event.location.city}".strip(' ,')
        else:
            lieu = 'Hybride'
    info_row('Lieu', lieu, row_y, '📍')

    row_y -= 9*mm
    # Mode participation
    mode_labels = {
        'onsite': '🏛️  Présentiel',
        'online': '🌐  En ligne',
        'both':   '🔀  Présentiel + En ligne',
    }
    mode_str = mode_labels.get(registration.participation_type, 'Présentiel')
    info_row('Participation', mode_str, row_y, '')

    row_y -= 9*mm
    # Participant
    info_row('Participant', participant.full_name, row_y, '👤')

    row_y -= 9*mm
    # Institution
    info_row('Institution', participant.institution or '—', row_y, '🏢')

    # ── Lien Zoom (si online ou both) ───────────────────────────
    y = bloc_y - 12*mm
    if registration.participation_type in ['online', 'both']:
        online_link = ''
        if event.location and event.location.online_link:
            online_link = event.location.online_link

        if online_link:
            c.setFillColor(colors.HexColor('#eff6ff'))
            c.roundRect(15*mm, y - 12*mm, w - 30*mm, 16*mm, 2*mm, fill=1, stroke=0)
            c.setStrokeColor(colors.HexColor('#3b82f6'))
            c.roundRect(15*mm, y - 12*mm, w - 30*mm, 16*mm, 2*mm, fill=0, stroke=1)
            c.setFont('Helvetica-Bold', 9)
            c.setFillColor(colors.HexColor('#1d4ed8'))
            c.drawString(20*mm, y - 2*mm, '🌐  Lien de connexion :')
            c.setFont('Helvetica', 9)
            c.setFillColor(colors.HexColor('#2563eb'))
            # Tronquer si trop long
            link_display = online_link if len(online_link) < 70 else online_link[:67] + '...'
            c.drawString(20*mm, y - 8*mm, link_display)
            y -= 20*mm

    # ── QR Code ─────────────────────────────────────────────────
    qr_size = 45*mm
    qr_x    = w/2 - qr_size/2
    qr_y    = y - qr_size - 10*mm

    # Cadre QR
    c.setFillColor(colors.white)
    c.setStrokeColor(VERT_LASPAD)
    c.setLineWidth(1.5)
    c.roundRect(qr_x - 5*mm, qr_y - 8*mm, qr_size + 10*mm, qr_size + 18*mm, 3*mm, fill=1, stroke=1)

    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    # Label sous QR
    c.setFont('Helvetica-Bold', 8)
    c.setFillColor(VERT_LASPAD)
    c.drawCentredString(w/2, qr_y - 5*mm, 'Scanner à l\'entrée')

    # Label au-dessus QR
    c.setFont('Helvetica', 8)
    c.setFillColor(colors.HexColor('#6b7280'))
    c.drawCentredString(w/2, qr_y + qr_size + 3*mm, 'Code d\'accès — valide une seule fois')

    # ── Pied de page ────────────────────────────────────────────
    footer_y = 15*mm
    c.setFillColor(GRIS_CLAIR)
    c.rect(0, 0, w, footer_y + 5*mm, fill=1, stroke=0)
    c.setStrokeColor(GRIS_BORD)
    c.setLineWidth(0.5)
    c.line(0, footer_y + 5*mm, w, footer_y + 5*mm)

    c.setFont('Helvetica', 7)
    c.setFillColor(colors.HexColor('#9ca3af'))
    c.drawCentredString(
        w/2, footer_y,
        f'Ce ticket est personnel et non transférable · {site_url}'
    )
    c.drawCentredString(
        w/2, footer_y - 4*mm,
        f'En cas de problème : communication@laspad.org'
    )

    c.save()
    buf.seek(0)
    return buf.read()


def save_ticket_pdf(registration) -> str:
    """
    Génère et sauvegarde le PDF dans media/tickets/.
    Retourne le chemin relatif au MEDIA_ROOT.
    """
    import os
    from django.core.files.base import ContentFile

    pdf_bytes = generate_ticket_pdf(registration)
    filename  = f"ticket_{registration.token}.pdf"

    # Sauvegarder via le FileField
    registration.ticket_pdf.save(filename, ContentFile(pdf_bytes), save=False)

    # Générer le numéro de ticket si absent
    if not registration.ticket_number:
        from django.utils import timezone
        year  = timezone.now().year
        count = registration.__class__.objects.filter(
            event=registration.event,
            status='accepte',
        ).count()
        registration.ticket_number = f"LASPAD-{year}-{count:04d}"

    registration.ticket_sent = False  # sera mis à True après envoi email
    registration.save(update_fields=['ticket_pdf', 'ticket_number', 'ticket_sent'])

    return registration.ticket_pdf.name

def generate_event_qr(event) -> str:
    """
    Génère un QR code du lien d'inscription avec le logo LASPAD au centre.
    Sauvegarde dans media/events/qrcodes/event_<pk>.png
    Retourne le chemin relatif au MEDIA_ROOT.
    """
    import os
    from django.conf import settings
    from django.core.files.base import ContentFile

    site_url = getattr(settings, 'SITE_URL', 'https://events.laspad.org')

    # URL du formulaire d'inscription
    registration_url = f"{site_url}{event.get_registration_url()}"

    # ── Générer le QR code ──
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # H = 30% correction (nécessaire pour logo)
        box_size=12,
        border=2,
    )
    qr.add_data(registration_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGBA')

    # ── Incruster le logo LASPAD au centre ──
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert('RGBA')

        # Taille du logo = 25% du QR
        qr_w, qr_h = qr_img.size
        logo_size   = int(qr_w * 0.25)
        logo        = logo.resize((logo_size, logo_size), Image.LANCZOS)

        # Fond blanc arrondi derrière le logo
        padding   = 10
        bg_size   = logo_size + padding * 2
        bg        = Image.new('RGBA', (bg_size, bg_size), (255, 255, 255, 255))

        # Coller le fond blanc puis le logo au centre du QR
        bg_pos    = ((qr_w - bg_size) // 2, (qr_h - bg_size) // 2)
        logo_pos  = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)

        qr_img.paste(bg,   bg_pos)
        qr_img.paste(logo, logo_pos, mask=logo)

    # ── Convertir en RGB et sauvegarder ──
    final = qr_img.convert('RGB')
    buf   = io.BytesIO()
    final.save(buf, format='PNG', dpi=(300, 300))
    buf.seek(0)

    # Sauvegarder dans media/events/qrcodes/
    filename     = f"event_{event.pk}_qr.png"
    save_dir     = os.path.join(settings.MEDIA_ROOT, 'events', 'qrcodes')
    os.makedirs(save_dir, exist_ok=True)
    full_path    = os.path.join(save_dir, filename)

    with open(full_path, 'wb') as f:
        f.write(buf.read())

    # Stocker le chemin relatif dans le modèle si le champ existe
    rel_path = f"events/qrcodes/{filename}"
    if hasattr(event, 'registration_qr'):
        event.registration_qr.name = rel_path
        event.save(update_fields=['registration_qr'])

    return rel_path