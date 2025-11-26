from datetime import datetime

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.routes.auth import login_required
from app.services.attendance_service import AttendanceService
from app.services.qr_service import QRService
from app.services.user_service import UserService

bp = Blueprint("user", __name__, url_prefix="/user")


def get_qr_service():
    """Obtener instancia de QRService con la configuración actual"""
    secret_key = current_app.config.get("QR_SECRET_KEY")
    if not secret_key:
        raise ValueError("QR_SECRET_KEY no está configurado")
    return QRService(secret_key)


@bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard del usuario con su código QR personal"""
    user_service = UserService()
    user = user_service.get(session.get("user_id"))

    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("auth.login"))

    # Generar código QR para el usuario
    qr_service = get_qr_service()
    qr_data = qr_service.create_qr_data(user.id)

    return render_template(
        "user/dashboard.html",
        title="Mi Dashboard",
        user=user,
        qr_token=qr_data["token"],
        qr_img=qr_data["image"],
        QR_EXPIRATION=current_app.config.get("QR_EXPIRATION", 60),
    )


@bp.route("/attendance")
@login_required
def attendance():
    """Historial de asistencias del usuario con filtros, paginación y exportación CSV"""
    import csv
    import io
    from datetime import datetime as dt

    user_service = UserService()
    attendance_service = AttendanceService()

    user = user_service.get(session.get("user_id"))

    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("auth.login"))

    # Parámetros de filtro por fecha
    start_date_str = request.args.get("start")
    end_date_str = request.args.get("end")

    # Paginación
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    try:
        per_page = max(1, min(100, int(request.args.get("per_page", "20"))))
    except ValueError:
        per_page = 20

    offset = (page - 1) * per_page

    # Obtener historial completo y aplicar filtros en memoria si se especifican fechas
    attendance_history = attendance_service.get_user_attendance(user.id)

    # Filtrar por rango de fechas si corresponde
    def parse_date(s: str):
        # Acepta formatos: YYYY-MM-DD o DD/MM/YYYY
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return dt.strptime(s, fmt).date()
            except ValueError:
                continue
        return None

    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None

    if start_date:
        attendance_history = [
            a for a in attendance_history if a.date and a.date >= start_date
        ]
    if end_date:
        attendance_history = [
            a for a in attendance_history if a.date and a.date <= end_date
        ]

    total_items = len(attendance_history)

    # Exportación CSV si se solicita
    if request.args.get("export") == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["user_id", "date", "timestamp"])
        for a in attendance_history:
            writer.writerow(
                [
                    a.user_id,
                    a.date.isoformat() if a.date else "",
                    a.timestamp.isoformat() if a.timestamp else "",
                ]
            )
        csv_data = output.getvalue()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=attendance.csv",
            },
        )

    # Aplicar paginación
    paginated = attendance_history[offset : offset + per_page]

    # Datos de paginación para el template
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total_items,
        "pages": (total_items + per_page - 1) // per_page if per_page else 1,
        "has_prev": page > 1,
        "has_next": offset + per_page < total_items,
    }

    return render_template(
        "user/attendance.html",
        title="Mi Asistencia",
        user=user,
        attendance_history=paginated,
        total_items=total_items,
        pagination=pagination,
        start_date=start_date_str or "",
        end_date=end_date_str or "",
    )


@bp.route("/profile")
@login_required
def profile():
    """Perfil del usuario"""
    user_service = UserService()
    user = user_service.get(session.get("user_id"))

    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("auth.login"))

    return render_template("user/profile.html", title="Mi Perfil", user=user)


@bp.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    """Actualizar perfil del usuario"""
    user_service = UserService()
    user_id = session.get("user_id")

    username = request.form.get("username")
    password = request.form.get("password")

    try:
        kwargs = {"username": username}
        if password:
            kwargs["password"] = password

        user_service.update(user_id, **kwargs)
        flash("Perfil actualizado exitosamente", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        current_app.logger.error(f"Error al actualizar perfil: {e}")
        flash("Error al actualizar perfil. Intente nuevamente.", "danger")

    return redirect(url_for("user.profile"))
