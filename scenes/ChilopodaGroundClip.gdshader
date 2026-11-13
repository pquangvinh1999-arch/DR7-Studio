shader_type canvas_item;
uniform bool clip_enabled = false;
uniform float clip_y = 0.0;
varying float pose_y;
void vertex() { pose_y = VERTEX.y; }
void fragment() {
	if (clip_enabled && pose_y > clip_y) { discard; }
	COLOR = texture(TEXTURE, UV);
}
