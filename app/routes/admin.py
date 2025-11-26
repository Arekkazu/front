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

from app.routes.auth import admin_required
from app.services.attendance_service import AttendanceService
from app.services.qr_service import QRService
from app.services.user_service import UserService

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Inicializar servicios que no dependen de current_app
user_service = UserService()
attendance_service = AttendanceService()


def get_qr_service():
    """Obtener instancia de QRService con la configuración actual"""
    secret_key = current_app.config.get("QR_SECRET_KEY")
    if not secret_key:
        raise ValueError("QR_SECRET_KEY no está configurado")
    return QRService(secret_key)


@bp.route("/dashboard")
@admin_required
def dashboard():
    users = user_service.get_all()
    return render_template(
        "admin/dashboard.html", users=users, title="Panel de Administración"
    )


@bp.route("/scanner")
@admin_required
def scanner():
    # Mostrar últimos registros de asistencia
    recent_attendance = AttendanceService().get_all()[:10]
    return render_template(
        "admin/scanner.html",
        title="Registrar Asistencia",
        recent_attendance=recent_attendance,
    )


@bp.route("/record_attendance", methods=["POST"])
@admin_required
def record_attendance():
    qr_token = request.form["qr_token"]
    qr_service = get_qr_service()

    # Validar token con el servicio QR
    user_id = qr_service.validate_qr_data(qr_token)

    if not user_id:
        flash(
            "Token QR inválido o expirado. Por favor, solicita un nuevo código.",
            "danger",
        )
        return redirect(url_for("admin.scanner"))

    # Obtener usuario
    user = user_service.get(user_id)
    if not user:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("admin.scanner"))

    try:
        # Intentar registrar asistencia
        attendance = attendance_service.create(user_id)
        flash(f"✅ Asistencia registrada exitosamente para {user.username}!", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        current_app.logger.error(f"Error al registrar asistencia: {e}")
        flash("Error al registrar asistencia. Intente nuevamente.", "danger")

    return redirect(url_for("admin.scanner"))


@bp.route("/attendance_list")
@admin_required
def attendance_list():
    """
    Lista de asistencias con filtros por fecha, paginación y exportación CSV
    Parámetros:
      - start: fecha inicio (YYYY-MM-DD o DD/MM/YYYY)
      - end: fecha fin (YYYY-MM-DD o DD/MM/YYYY)
      - page: número de página (por defecto 1)
      - per_page: registros por página (por defecto 20, máx 100)
      - export=csv: exporta el resultado filtrado a CSV
    """
    import csv
    import io
    from datetime import datetime as dt

    attendance_service = AttendanceService()

    # Filtros
    start_date_str = request.args.get("start")
    end_date_str = request.args.get("end")

    def parse_date(s: str):
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return dt.strptime(s, fmt).date()
            except ValueError:
                continue
        return None

    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)

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

    # Obtener todos (ordenados desc por fecha en repo) y filtrar en memoria
    all_attendance = attendance_service.get_all()

    if start_date:
        all_attendance = [a for a in all_attendance if a.date and a.date >= start_date]
    if end_date:
        all_attendance = [a for a in all_attendance if a.date and a.date <= end_date]

    total_items = len(all_attendance)

    # Exportación CSV
    if request.args.get("export") == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["user_id", "date", "timestamp"])
        for a in all_attendance:
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
            headers={"Content-Disposition": "attachment; filename=attendances.csv"},
        )

    # Paginar
    paginated = all_attendance[offset : offset + per_page]
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total_items,
        "pages": (total_items + per_page - 1) // per_page if per_page else 1,
        "has_prev": page > 1,
        "has_next": offset + per_page < total_items,
    }

    return render_template(
        "admin/attendance_list.html",
        title="Asistencias",
        attendance_history=paginated,
        pagination=pagination,
        start_date=start_date_str or "",
        end_date=end_date_str or "",
        total_items=total_items,
    )


@bp.route("/add_user", methods=["POST"])
@admin_required
def add_user():
    username = request.form.get("username")
    password = request.form.get("password")
    role_name = request.form.get("role")

    if not all([username, password, role_name]):
        flash("Todos los campos son requeridos", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        # Crear usuario con el servicio
        user = user_service.create(username, password, role_name)
        flash(
            f'Usuario "{user.username}" creado exitosamente como {role_name}', "success"
        )
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        current_app.logger.error(f"Error al crear usuario: {e}")
        flash("Error al crear usuario. Intente nuevamente.", "danger")

    return redirect(url_for("admin.dashboard"))


@bp.route("/edit_user", methods=["POST"])
@admin_required
def edit_user():
    user_id_str = request.form.get("user_id")
    username = request.form.get("username")
    password = request.form.get("password")
    role_name = request.form.get("role")

    if not user_id_str:
        flash("ID de usuario requerido", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        user_id = int(user_id_str)
        # Actualizar usuario con el servicio
        kwargs = {"username": username}
        if password:
            kwargs["password"] = password
        if role_name:
            kwargs["role_name"] = role_name

        updated_user = user_service.update(user_id, **kwargs)
        flash(f'Usuario "{updated_user.username}" actualizado exitosamente', "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        current_app.logger.error(f"Error al actualizar usuario: {e}")
        flash("Error al actualizar usuario. Intente nuevamente.", "danger")

    return redirect(url_for("admin.dashboard"))


@bp.route("/delete_user", methods=["POST"])
@admin_required
def delete_user():
    user_id_str = request.form.get("user_id")

    if not user_id_str:
        flash("ID de usuario requerido", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        user_id = int(user_id_str)
        # No permitir eliminar al usuario actual
        if user_id == session.get("user_id"):
            flash(
                "No puedes eliminar tu propia cuenta mientras estás conectado", "danger"
            )
            return redirect(url_for("admin.dashboard"))

        # Verificar si es el único admin
        if user_service.is_last_admin(user_id):
            flash("No puedes eliminar el único administrador del sistema", "danger")
            return redirect(url_for("admin.dashboard"))

        # Eliminar usuario
        user_service.delete(user_id)
        flash("Usuario eliminado permanentemente", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        current_app.logger.error(f"Error al eliminar usuario: {e}")
        flash("Error al eliminar usuario. Intente nuevamente.", "danger")

    return redirect(url_for("admin.dashboard"))
