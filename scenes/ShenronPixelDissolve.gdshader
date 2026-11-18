shader_type canvas_item;
render_mode unshaded;
uniform sampler2D threshold_mask : filter_nearest, repeat_disable;
uniform vec2 canvas_anchor = vec2(192.0, 240.0);
uniform vec2 mask_size = vec2(96.0, 68.0);
uniform float cell_size = 4.0;
uniform float progress : hint_range(0.0, 1.0) = 0.0;
uniform float edge_width = 0.07;
uniform vec4 edge_color : source_color = vec4(1.0, 0.92549, 0.61176, 1.0);
varying vec2 canvas_pixel;
void vertex() {
    canvas_pixel = VERTEX + canvas_anchor;
}
void fragment() {
    vec4 original = texture(TEXTURE, UV);
    if (progress >= 1.0) {
        COLOR = original;
    } else {
        vec2 cell = floor(canvas_pixel / cell_size);
        float threshold = (texture(threshold_mask, (cell + vec2(0.5)) / mask_size).r * 255.0 + 0.5) / 256.0;
        if (progress < threshold) {
            COLOR = vec4(0.0);
        } else {
            float edge = clamp(1.0 - (progress - threshold) / edge_width, 0.0, 1.0);
            COLOR = vec4(mix(original.rgb, edge_color.rgb, edge * 0.85), original.a);
        }
    }
}
