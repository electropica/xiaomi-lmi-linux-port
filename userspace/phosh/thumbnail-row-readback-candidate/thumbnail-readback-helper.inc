/* Read GLES thumbnails row by row through wlroots' padded-stride path.
 * Restrict this workaround to 32-bit ARGB GLES textures; other renderers and
 * formats keep the original API call. No output/screen rendering is changed.
 */
static bool
phoc_renderer_read_thumbnail_pixels (struct wlr_texture *texture,
                                     void *data,
                                     uint32_t format,
                                     size_t stride,
                                     int32_t width,
                                     int32_t height)
{
  uint32_t row_bytes, read_stride;
  unsigned char *staging;
  bool success;

  if (!texture || !data || width <= 0 || height <= 0 || stride > G_MAXUINT32)
    return false;

  if (format != DRM_FORMAT_ARGB8888 || !wlr_texture_is_gles2 (texture))
    return wlr_texture_read_pixels (texture, &(struct wlr_texture_read_pixels_options) {
        .data = data, .format = format, .stride = stride,
        .src_box = { .x = 0, .y = 0, .width = width, .height = height },
      });

  if ((uint32_t) width > (G_MAXUINT32 - 4) / 4)
    return false;
  row_bytes = (uint32_t) width * 4;
  if (stride < row_bytes)
    return false;

  /* A different destination stride selects wlroots 0.18 GLES2's row loop,
   * avoiding its one-call glReadPixels path. Never expose this private pitch
   * to the client: copy only the real pixels back to the client's stride.
   */
  read_stride = row_bytes + 4;
  staging = g_try_malloc_n ((size_t) height, read_stride);
  if (!staging)
    return false;

  success = wlr_texture_read_pixels (texture, &(struct wlr_texture_read_pixels_options) {
      .data = staging, .format = format, .stride = read_stride,
      .src_box = { .x = 0, .y = 0, .width = width, .height = height },
    });
  if (success) {
    for (int32_t y = 0; y < height; y++)
      memcpy ((unsigned char *) data + (size_t) y * stride,
              staging + (size_t) y * read_stride,
              row_bytes);
  }
  g_free (staging);
  return success;
}
