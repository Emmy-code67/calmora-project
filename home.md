# Route change: app/main/routes.py

Replace the existing `index` view with this (only change: guests now see the
landing page instead of being redirected to the login form):

```python
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/home.html")
```

Nothing else changes. `render_template` and `redirect/url_for` are already
imported in that file.

