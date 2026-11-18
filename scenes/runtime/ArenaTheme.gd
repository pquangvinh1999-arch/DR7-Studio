class_name ArenaTheme
extends RefCounted
## Shared Godot Theme for ArenaSandbox UI:
## - Prepared for "Spiegel" font (res://assets/fonts/Spiegel.ttf when provided), falling back cleanly to Godot default font.
## - +30% larger font sizes (~21px base vs 16px) with crisp outline & frosted-glass panel/button styling.

const SPIEGEL_FONT_CANDIDATES := [
	"res://assets/fonts/Spiegel.ttf",
	"res://assets/fonts/Spiegel.otf",
	"res://assets/fonts/Spiegel-Regular.ttf",
	"res://assets/fonts/Spiegel_TT_Regular.ttf",
]


static func load_spiegel_font() -> Font:
	for p in SPIEGEL_FONT_CANDIDATES:
		if ResourceLoader.exists(p):
			var loaded := ResourceLoader.load(p)
			if loaded is Font:
				return loaded
	return null


static func make_frosted_style(bg_alpha: float = 0.72, border_color: Color = Color(0.78, 0.88, 1.0, 0.28), radius: int = 10) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.06, 0.10, 0.17, bg_alpha)
	sb.border_color = border_color
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(radius)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 6
	sb.content_margin_bottom = 6
	return sb


static func build_theme() -> Theme:
	var theme := Theme.new()
	var font := load_spiegel_font()
	if font != null:
		theme.default_font = font
	# +30% larger & crisper text than Godot's default 16px
	theme.default_font_size = 21

	var outline_col := Color(0.02, 0.04, 0.09, 0.94)
	var shadow_col := Color(0.0, 0.0, 0.0, 0.78)
	for cls in ["Label", "Button", "OptionButton"]:
		theme.set_font_size("font_size", cls, 21)
		theme.set_color("font_color", cls, Color(0.96, 0.98, 1.0, 1.0))
		theme.set_color("font_outline_color", cls, outline_col)
		theme.set_constant("outline_size", cls, 3)
		theme.set_color("font_shadow_color", cls, shadow_col)
		theme.set_constant("shadow_offset_x", cls, 1)
		theme.set_constant("shadow_offset_y", cls, 1)

	var btn_normal := make_frosted_style(0.68, Color(0.75, 0.86, 1.0, 0.26), 10)
	var btn_hover := make_frosted_style(0.82, Color(0.38, 0.82, 1.0, 0.60), 10)
	var btn_pressed := make_frosted_style(0.92, Color(0.98, 0.80, 0.25, 0.85), 10)
	var btn_disabled := make_frosted_style(0.36, Color(0.55, 0.62, 0.72, 0.18), 10)
	for cls in ["Button", "OptionButton"]:
		theme.set_stylebox("normal", cls, btn_normal)
		theme.set_stylebox("hover", cls, btn_hover)
		theme.set_stylebox("pressed", cls, btn_pressed)
		theme.set_stylebox("disabled", cls, btn_disabled)
		theme.set_color("font_disabled_color", cls, Color(0.62, 0.68, 0.78, 0.65))

	theme.set_stylebox("panel", "PanelContainer", make_frosted_style(0.76, Color(0.70, 0.85, 1.0, 0.30), 12))
	return theme
