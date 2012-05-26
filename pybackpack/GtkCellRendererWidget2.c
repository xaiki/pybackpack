/* GTK - The GIMP Toolkit
 *
 * Copyright (C) 2009 Matthias Clasen <mclasen@redhat.com>
 * Copyright (C) 2008 Richard Hughes <richard@hughsie.com>
 * Copyright (C) 2009 Bastien Nocera <hadess@hadess.net>
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.         See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Modified by the GTK+ Team and others 2007.  See the AUTHORS
 * file for a list of people on the GTK+ Team.  See the ChangeLog
 * files for a list of changes.  These files are distributed with
 * GTK+ at ftp://ftp.gtk.org/pub/gtk/.
 */
/*
#include "config.h"

#include "gtkcellrendererwidget.h"
#include "gtkiconfactory.h"
#include "gtkicontheme.h"
#include "gtkintl.h"
#include "gtksettings.h"
#include "gtktypebuiltins.h"

#undef GDK_DEPRECATED
#undef GDK_DEPRECATED_FOR
#define GDK_DEPRECATED
#define GDK_DEPRECATED_FOR(f)

#include "deprecated/gtkstyle.h"
*/

#include "GtkCellRendererWidget2.h"
#include "gtk/gtk.h"

/**
 * SECTION:gtkcellrendererwidget
 * @Short_description: Renders a spinning animation in a cell
 * @Title: GtkCellRendererWidget
 * @See_also: #GtkWidget, #GtkCellRendererProgress
 *
 * GtkCellRendererWidget renders a spinning animation in a cell, very
 * similar to #GtkWidget. It can often be used as an alternative
 * to a #GtkCellRendererProgress for displaying indefinite activity,
 * instead of actual progress.
 *
 * To start the animation in a cell, set the #GtkCellRendererWidget:active
 * property to %TRUE and increment the #GtkCellRendererWidget:pulse property
 * at regular intervals. The usual way to set the cell renderer properties
 * for each cell is to bind them to columns in your tree model using e.g.
 * gtk_tree_view_column_add_attribute().
 */

#define xatrace() printf("%s:%d:%s():\n" , __FILE__, __LINE__, __func__)

enum {
  PROP_0,
  PROP_WIDGET,
  PROP_ACTIVE,
  PROP_PULSE,
  PROP_SIZE
};

struct _GtkCellRendererWidgetPrivate
{
	GtkWidget *widget;
  gboolean active;
  guint pulse;
  GtkIconSize icon_size, old_icon_size;
  gint size;
};


static void gtk_cell_renderer_widget_get_property (GObject         *object,
                                                    guint            param_id,
                                                    GValue          *value,
                                                    GParamSpec      *pspec);
static void gtk_cell_renderer_widget_set_property (GObject         *object,
                                                    guint            param_id,
                                                    const GValue    *value,
                                                    GParamSpec      *pspec);
static void gtk_cell_renderer_widget_get_size     (GtkCellRenderer *cell,
                                                    GtkWidget          *widget,
                                                    const GdkRectangle *cell_area,
                                                    gint               *x_offset,
                                                    gint               *y_offset,
                                                    gint               *width,
                                                    gint               *height);
static GtkCellEditable *
gtk_cell_renderer_widget_start_editing (GtkCellRenderer     *cell,
                                       GdkEvent            *event,
                                       GtkWidget           *widget,
                                       const gchar         *path,
                                       const GdkRectangle  *background_area,
                                       const GdkRectangle  *cell_area,
                                       GtkCellRendererState flags);

static void gtk_cell_renderer_widget_render       (GtkCellRenderer      *cell,
                                                    cairo_t              *cr,
                                                    GtkWidget            *widget,
                                                    const GdkRectangle   *background_area,
                                                    const GdkRectangle   *cell_area,
                                                    GtkCellRendererState  flags);

G_DEFINE_TYPE (GtkCellRendererWidget, gtk_cell_renderer_widget, GTK_TYPE_CELL_RENDERER)

static void
gtk_cell_renderer_widget_class_init (GtkCellRendererWidgetClass *klass)
{
  xatrace();
  GObjectClass *object_class = G_OBJECT_CLASS (klass);
  GtkCellRendererClass *cell_class = GTK_CELL_RENDERER_CLASS (klass);

  object_class->get_property = gtk_cell_renderer_widget_get_property;
  object_class->set_property = gtk_cell_renderer_widget_set_property;

  cell_class->get_size = gtk_cell_renderer_widget_get_size;
  cell_class->render = gtk_cell_renderer_widget_render;
  cell_class->start_editing = gtk_cell_renderer_widget_start_editing;

  /* GtkCellRendererWidget:active:
   *
   * Whether the widget is active (ie. shown) in the cell
   *
   * Since: 2.20
   */
  g_object_class_install_property (object_class,
                                   PROP_ACTIVE,
                                   g_param_spec_boolean ("active",
                                                         "Active",
                                                         "Whether the widget is active (ie. shown) in the cell",
                                                         FALSE,
                                                         G_PARAM_READWRITE));
  /**
   * GtkCellRendererWidget:widget:
   *
   * the #GtkWidget to attach to this cell.
   * Ideally this should be automatic, but there is still lots of vodo for me there.
   *
   * Since: 3.6
   */
  g_object_class_install_property (object_class,
                                   PROP_WIDGET,
                                   g_param_spec_object ("widget",
							"Widget",
							"GtkWidget to attach",
							GTK_TYPE_WIDGET,
							G_PARAM_READWRITE));
  /**
   * GtkCellRendererWidget:size:
   *
   * The #GtkIconSize value that specifies the size of the rendered widget.
   *
   * Since: 2.20
   */
  g_object_class_install_property (object_class,
                                   PROP_SIZE,
                                   g_param_spec_enum ("size",
                                                      "Size",
                                                      "The GtkIconSize value that specifies the size of the rendered widget",
                                                      GTK_TYPE_ICON_SIZE, GTK_ICON_SIZE_MENU,
                                                      G_PARAM_READWRITE));


  g_type_class_add_private (object_class, sizeof (GtkCellRendererWidgetPrivate));
}

static void
gtk_cell_renderer_widget_init (GtkCellRendererWidget *cell)
{
  xatrace();
  cell->priv = G_TYPE_INSTANCE_GET_PRIVATE (cell,
                                            GTK_TYPE_CELL_RENDERER_WIDGET,
                                            GtkCellRendererWidgetPrivate);

  cell->priv->pulse = 0;
  cell->priv->old_icon_size = GTK_ICON_SIZE_INVALID;
  cell->priv->icon_size = GTK_ICON_SIZE_MENU;
}

/**
 * gtk_cell_renderer_widget_new:
 *
 * Returns a new cell renderer which will show a widget to indicate
 * activity.
 *
 * Return value: a new #GtkCellRenderer
 *
 * Since: 2.20
 */
GtkCellRenderer *
gtk_cell_renderer_widget_new (void)
{
  xatrace();  return g_object_new (GTK_TYPE_CELL_RENDERER_WIDGET, NULL);
}

static void
gtk_cell_renderer_widget_update_size (GtkCellRendererWidget *cell,
                                       GtkWidget              *widget)
{
  xatrace();  GtkCellRendererWidgetPrivate *priv = cell->priv;
  GdkScreen *screen;
  GtkSettings *settings;

  if (priv->old_icon_size == priv->icon_size)
    return;

  screen = gtk_widget_get_screen (GTK_WIDGET (widget));
  settings = gtk_settings_get_for_screen (screen);

  if (!gtk_icon_size_lookup_for_settings (settings, priv->icon_size, &priv->size, NULL))
    {
      g_warning ("Invalid icon size %u\n", priv->icon_size);
      priv->size = 24;
    }
}

static void
gtk_cell_renderer_widget_get_property (GObject    *object,
                                        guint       param_id,
                                        GValue     *value,
                                        GParamSpec *pspec)
{
  xatrace();  GtkCellRendererWidget *cell = GTK_CELL_RENDERER_WIDGET (object);
  GtkCellRendererWidgetPrivate *priv = cell->priv;

  switch (param_id)
    {
    case PROP_WIDGET:
      g_value_set_object (value, priv->widget);
      break;
    case PROP_ACTIVE:
      g_value_set_boolean (value, priv->active);
      break;
    case PROP_PULSE:
      g_value_set_uint (value, priv->pulse);
      break;
    case PROP_SIZE:
      g_value_set_enum (value, priv->icon_size);
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, param_id, pspec);
    }
}

static void
gtk_cell_renderer_widget_set_property (GObject      *object,
                                        guint         param_id,
                                        const GValue *value,
                                        GParamSpec   *pspec)
{
  xatrace();  GtkCellRendererWidget *cell = GTK_CELL_RENDERER_WIDGET (object);
  GtkCellRendererWidgetPrivate *priv = cell->priv;

  switch (param_id)
    {
    case PROP_WIDGET:
	    priv->widget = g_value_get_object (value);
	    printf ("setting widget to: %p\n", priv->widget);
      break;
    case PROP_ACTIVE:
	    priv->active = g_value_get_boolean (value);
	    break;
    case PROP_PULSE:
	    priv->pulse = g_value_get_uint (value);
	    break;
    case PROP_SIZE:
	    priv->old_icon_size = priv->icon_size;
	    priv->icon_size = g_value_get_enum (value);
	    break;
    default:
	    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, param_id, pspec);
    }
}

static void
gtk_cell_renderer_widget_get_size (GtkCellRenderer    *cellr,
                                    GtkWidget          *widget,
                                    const GdkRectangle *cell_area,
                                    gint               *x_offset,
                                    gint               *y_offset,
                                    gint               *width,
                                    gint               *height)
{
  xatrace();  GtkCellRendererWidget *cell = GTK_CELL_RENDERER_WIDGET (cellr);
  GtkCellRendererWidgetPrivate *priv = cell->priv;
  gdouble align;
  gint w, h;
  gint xpad, ypad;
  gfloat xalign, yalign;
  gboolean rtl;

  rtl = gtk_widget_get_direction (widget) == GTK_TEXT_DIR_RTL;

  gtk_cell_renderer_widget_update_size (cell, widget);

  g_object_get (cellr,
                "xpad", &xpad,
                "ypad", &ypad,
                "xalign", &xalign,
                "yalign", &yalign,
                NULL);
  w = h = priv->size;

  if (cell_area)
    {
      if (x_offset)
        {
          align = rtl ? 1.0 - xalign : xalign;
          *x_offset = align * (cell_area->width - w);
          *x_offset = MAX (*x_offset, 0);
        }
      if (y_offset)
        {
          align = rtl ? 1.0 - yalign : yalign;
          *y_offset = align * (cell_area->height - h);
          *y_offset = MAX (*y_offset, 0);
        }
    }
  else
    {
      if (x_offset)
        *x_offset = 0;
      if (y_offset)
        *y_offset = 0;
    }

  if (width)
    *width = w;
  if (height)
    *height = h;
}

#define GTK_CELL_RENDERER_WIDGET_PATH "gtk-cell-renderer-widget-path"

static GtkCellEditable *
gtk_cell_renderer_widget_start_editing (GtkCellRenderer     *cellr,
                                       GdkEvent            *event,
                                       GtkWidget           *treeview,
                                       const gchar         *path,
                                       const GdkRectangle  *background_area,
                                       const GdkRectangle  *cell_area,
                                       GtkCellRendererState flags)
{
  xatrace();  GtkCellRendererWidget *cell = GTK_CELL_RENDERER_WIDGET (cellr);
  GtkCellRendererWidgetPrivate *priv = cell->priv;
  GtkWidget *widget = priv->widget;

  if (!widget)
    printf ("NO WIDGET !!!!\n");

  g_object_set_data_full (G_OBJECT (widget),
                          GTK_CELL_RENDERER_WIDGET_PATH,
                          g_strdup (path), g_free);

  gtk_widget_show(widget);

  return GTK_CELL_EDITABLE (widget);
}

static void
gtk_cell_renderer_text_render_redux (GtkWidget            *label,
                                     GtkCellRenderer      *cellr,
                                     cairo_t              *cr,
                                     GtkWidget            *widget,
                                     const GdkRectangle   *background_area,
                                     const GdkRectangle   *cell_area,
                                     GtkCellRendererState  flags)
{
  xatrace();
  GtkStyleContext *context;
  PangoLayout *layout;
  GdkRGBA background;
  gint x_offset = 0;
  gint y_offset = 0;
  gint xpad, ypad;
  PangoRectangle rect;

  layout = gtk_label_get_layout (GTK_LABEL (label));
  printf ("label: %p, %s\n", layout, gtk_label_get_text (GTK_LABEL(label)));
//  get_size (cell, widget, cell_area, layout, &x_offset, &y_offset, NULL, NULL);
  context = gtk_widget_get_style_context (widget);

  if ((flags & GTK_CELL_RENDERER_SELECTED) == 0)
    {
      gdk_cairo_rectangle (cr, background_area);
      gdk_cairo_set_source_rgba (cr, &background);
      cairo_fill (cr);
    }

  gtk_cell_renderer_get_padding (cellr, &xpad, &ypad);

  if (gtk_label_get_ellipsize (GTK_LABEL(label))) {
      pango_layout_set_width (layout,
                              (cell_area->width - x_offset - 2 * xpad) * PANGO_SCALE);
  } else if (gtk_label_get_line_wrap (GTK_LABEL(label))) {
        pango_layout_set_width (layout, -1);
  }

  pango_layout_get_pixel_extents (layout, NULL, &rect);
  x_offset = x_offset - rect.x;

  cairo_save (cr);

  gdk_cairo_rectangle (cr, cell_area);
  cairo_clip (cr);

  gtk_render_layout (context, cr,
                     cell_area->x + x_offset + xpad,
                     cell_area->y + y_offset + ypad,
                     layout);

  cairo_restore (cr);
}

static void
gtk_cell_renderer_spinner_render_redux (GtkWidget            *spinner,
                                        GtkCellRenderer      *cellr,
                                        cairo_t              *cr,
                                        GtkWidget            *widget,
                                        const GdkRectangle   *background_area,
                                        const GdkRectangle   *cell_area,
                                        GtkCellRendererState  flags)
{
  xatrace();
  GtkStateType state;
  GdkRectangle pix_rect;
  GdkRectangle draw_rect;
  GtkAllocation alloc;
  gint xpad, ypad;


  gtk_cell_renderer_widget_get_size (cellr, widget, (GdkRectangle *) cell_area,
                                      &pix_rect.x, &pix_rect.y,
                                      &pix_rect.width, &pix_rect.height);

  g_object_get (cellr,
                "xpad", &xpad,
                "ypad", &ypad,
                NULL);
  pix_rect.x += cell_area->x + xpad;
  pix_rect.y += cell_area->y + ypad;
  pix_rect.width -= xpad * 2;
  pix_rect.height -= ypad * 2;

  if (!gdk_rectangle_intersect (cell_area, &pix_rect, &draw_rect))
    return;

  state = GTK_STATE_NORMAL;
  if (gtk_widget_get_state (widget) == GTK_STATE_INSENSITIVE ||
      !gtk_cell_renderer_get_sensitive (cellr))
    {
      state = GTK_STATE_INSENSITIVE;
    }
  else
    {
      if ((flags & GTK_CELL_RENDERER_SELECTED) != 0)
        {
          if (gtk_widget_has_focus (widget))
            state = GTK_STATE_SELECTED;
          else
            state = GTK_STATE_ACTIVE;
        }
      else
        state = GTK_STATE_PRELIGHT;
    }

  cairo_save (cr);

  gdk_cairo_rectangle (cr, cell_area);
  cairo_clip (cr);

  gtk_paint_spinner (gtk_widget_get_style (widget),
                     cr,
                     state,
                     widget,
                     "cell",
                     0,
                     draw_rect.x, draw_rect.y,
                     draw_rect.width, draw_rect.height);

  cairo_restore (cr);
}

static inline gdouble
get_progress_bar_size (gdouble pulse,
                       gdouble value,
                       gdouble full_size)
{
  gdouble bar_size;

  if (pulse < 0)
    bar_size = full_size * MAX (0, value) / 100;
  else if (pulse == 0)
    bar_size = 0;
  else if (pulse == G_MAXINT)
    bar_size = full_size;
  else
    bar_size = MAX (2, full_size / 5);

  return bar_size;
}

static inline gint
get_progress_bar_position (gint     start,
                           gint     full_size,
                           gint     bar_size,
                           gdouble  pulse,
                           gboolean is_rtl)
{
  gint position;
  guint ipulse = (guint) pulse;

  if (pulse < 0 || pulse == 0 || pulse == G_MAXINT)
    {
      position = is_rtl ? (start + full_size - bar_size) : start;
    }
  else
    {
      position = (is_rtl ? ipulse + 12 : ipulse) % 24;
      if (position > 12)
        position = 24 - position;
      position = start + full_size * position / 15;
    }

  return position;
}


static void
gtk_cell_renderer_progress_render_redux (GtkWidget            *progress,
                                         GtkCellRenderer      *cellr,
                                         cairo_t              *cr,
                                         GtkWidget            *widget,
                                         const GdkRectangle   *background_area,
                                         const GdkRectangle   *cell_area,
                                         GtkCellRendererState  flags)
{
  xatrace();

  GtkStyleContext *context;
  GtkBorder padding;
  PangoLayout *layout;
  PangoRectangle logical_rect;
  gint x, y, w, h, x_pos, y_pos, bar_position, start;
  gdouble bar_size, full_size;
  gint xpad, ypad;
  GdkRectangle clip;
  gboolean is_rtl;

  gdouble pulse = gtk_progress_bar_get_pulse_step (GTK_PROGRESS_BAR(progress));
  gdouble value = gtk_progress_bar_get_fraction (GTK_PROGRESS_BAR(progress));
  gboolean inverted = gtk_progress_bar_get_inverted(GTK_PROGRESS_BAR(progress));
  const gchar *label = gtk_progress_bar_get_text (GTK_PROGRESS_BAR(progress));
  GtkOrientation orientation = gtk_orientable_get_orientation (GTK_ORIENTABLE(progress));

  context = gtk_widget_get_style_context (widget);
  is_rtl = gtk_widget_get_direction (widget) == GTK_TEXT_DIR_RTL;

  gtk_cell_renderer_get_padding (cellr, &xpad, &ypad);
  x = cell_area->x + xpad;
  y = cell_area->y + ypad;
  w = cell_area->width - xpad * 2;
  h = cell_area->height - ypad * 2;

  gtk_style_context_save (context);
  gtk_style_context_add_class (context, GTK_STYLE_CLASS_TROUGH);

  gtk_render_background (context, cr, x, y, w, h);
  gtk_render_frame (context, cr, x, y, w, h);

  gtk_style_context_get_padding (context, GTK_STATE_FLAG_NORMAL, &padding);

  x += padding.left;
  y += padding.top;
  w -= padding.left + padding.right;
  h -= padding.top + padding.bottom;

  gtk_style_context_restore (context);

  if (orientation == GTK_ORIENTATION_HORIZONTAL)
    {
      clip.y = y;
      clip.height = h;

      start = x;
      full_size = w;

      bar_size = get_progress_bar_size (pulse, value, full_size);

      if (inverted)
        bar_position = get_progress_bar_position (start, full_size, bar_size,
                                                  pulse, is_rtl);
      else
	bar_position = get_progress_bar_position (start, full_size, bar_size,
                                            pulse, !is_rtl);

      clip.width = bar_size;
      clip.x = bar_position;
    }
  else
    {
      clip.x = x;
      clip.width = w;

      start = y;
      full_size = h;

      bar_size = get_progress_bar_size (pulse, value, full_size);

      if (inverted)
        bar_position = get_progress_bar_position (start, full_size, bar_size,
                                         pulse, TRUE);
      else
        bar_position = get_progress_bar_position (start, full_size, bar_size,
                                         pulse, FALSE);

      clip.height = bar_size;
      clip.y = bar_position;
    }

  gtk_style_context_save (context);
  gtk_style_context_add_class (context, GTK_STYLE_CLASS_PROGRESSBAR);

  if (bar_size > 0)
    gtk_render_activity (context, cr,
                         clip.x, clip.y,
                         clip.width, clip.height);

  gtk_style_context_restore (context);

  if (label)
    {
      gfloat text_xalign;

      layout = gtk_widget_create_pango_layout (widget, label);
      pango_layout_get_pixel_extents (layout, NULL, &logical_rect);

      if (gtk_widget_get_direction (widget) != GTK_TEXT_DIR_LTR)
        text_xalign = 1.0;
      else
        text_xalign = 0;

      x_pos = x + padding.left + text_xalign *
        (w - padding.left - padding.right - logical_rect.width);

      y_pos = y + padding.top;

      cairo_save (cr);
      gdk_cairo_rectangle (cr, &clip);
      cairo_clip (cr);

      gtk_style_context_save (context);
      gtk_style_context_add_class (context, GTK_STYLE_CLASS_PROGRESSBAR);

      gtk_render_layout (context, cr,
                         x_pos, y_pos,
                         layout);

      gtk_style_context_restore (context);
      cairo_restore (cr);

      gtk_style_context_save (context);
      gtk_style_context_add_class (context, GTK_STYLE_CLASS_TROUGH);

      if (bar_position > start)
        {
	  if (orientation == GTK_ORIENTATION_HORIZONTAL)
	    {
	      clip.x = x;
	      clip.width = bar_position - x;
	    }
	  else
	    {
	      clip.y = y;
	      clip.height = bar_position - y;
	    }

          cairo_save (cr);
          gdk_cairo_rectangle (cr, &clip);
          cairo_clip (cr);

          gtk_render_layout (context, cr,
                             x_pos, y_pos,
                             layout);

          cairo_restore (cr);
        }

      if (bar_position + bar_size < start + full_size)
        {
	  if (orientation == GTK_ORIENTATION_HORIZONTAL)
	    {
	      clip.x = bar_position + bar_size;
	      clip.width = x + w - (bar_position + bar_size);
	    }
	  else
	    {
	      clip.y = bar_position + bar_size;
	      clip.height = y + h - (bar_position + bar_size);
	    }

          cairo_save (cr);
          gdk_cairo_rectangle (cr, &clip);
          cairo_clip (cr);

          gtk_render_layout (context, cr,
                             x_pos, y_pos,
                             layout);

          cairo_restore (cr);
        }

      gtk_style_context_restore (context);
      g_object_unref (layout);
    }
}

static void
gtk_cell_renderer_toggle_get_size (GtkCellRenderer    *cell,
				   GtkWidget          *widget,
				   const GdkRectangle *cell_area,
				   gint               *x_offset,
				   gint               *y_offset,
				   gint               *width,
				   gint               *height)
{
  GtkCellRendererWidgetPrivate *priv;
  gint calc_width;
  gint calc_height;
  gint xpad, ypad;

  priv = GTK_CELL_RENDERER_WIDGET (cell)->priv;

  gtk_cell_renderer_get_padding (cell, &xpad, &ypad);
  calc_width = xpad * 2;
  calc_height = ypad * 2;

  if (width)
    *width = calc_width;

  if (height)
    *height = calc_height;

  if (cell_area)
    {
      gfloat xalign, yalign;

      gtk_cell_renderer_get_alignment (cell, &xalign, &yalign);

      if (x_offset)
	{
	  *x_offset = ((gtk_widget_get_direction (widget) == GTK_TEXT_DIR_RTL) ?
		       (1.0 - xalign) : xalign) * (cell_area->width - calc_width);
	  *x_offset = MAX (*x_offset, 0);
	}
      if (y_offset)
	{
	  *y_offset = yalign * (cell_area->height - calc_height);
	  *y_offset = MAX (*y_offset, 0);
	}
    }
  else
    {
      if (x_offset) *x_offset = 0;
      if (y_offset) *y_offset = 0;
    }
}

static void
gtk_cell_renderer_toggle_render_redux (GtkWidget            *toggle,
                                       GtkCellRenderer      *cellr,
                                       cairo_t              *cr,
                                       GtkWidget            *widget,
                                       const GdkRectangle   *background_area,
                                       const GdkRectangle   *cell_area,
                                       GtkCellRendererState  flags)
{
  xatrace();
  gboolean radio = FALSE; /* XXX:(xaiki) HACK */

  GtkStyleContext *context;
  gint width, height;
  gint x_offset, y_offset;
  gint xpad, ypad;
  GtkStateFlags state = gtk_widget_get_state_flags (GTK_WIDGET (toggle));

  context = gtk_widget_get_style_context (widget);
  gtk_cell_renderer_toggle_get_size (cellr, widget, cell_area,
                                     &x_offset, &y_offset,
                                     &width, &height);
  gtk_cell_renderer_get_padding (cellr, &xpad, &ypad);
  width -= xpad * 2;
  height -= ypad * 2;

  if (width <= 0 || height <= 0)
    return;

  state = gtk_cell_renderer_get_state (cellr, widget, flags);

  cairo_save (cr);

  gdk_cairo_rectangle (cr, cell_area);
  cairo_clip (cr);

  gtk_style_context_save (context);
  gtk_style_context_set_state (context, state);

  if (radio)
    {
      gtk_style_context_add_class (context, GTK_STYLE_CLASS_RADIO);
      gtk_render_option (context, cr,
                         cell_area->x + x_offset + xpad,
                         cell_area->y + y_offset + ypad,
                         width, height);
    }
  else
    {
      gtk_style_context_add_class (context, GTK_STYLE_CLASS_CHECK);
      gtk_render_check (context, cr,
                        cell_area->x + x_offset + xpad,
                        cell_area->y + y_offset + ypad,
                        width, height);
    }

  gtk_style_context_restore (context);
  cairo_restore (cr);
}

static void
gtk_cell_renderer_widget_render_internal (GtkWidget 			     *widget,
                                          GtkCellRenderer      *cellr,
                                          cairo_t              *cr,
                                          GtkWidget            *treeview,
                                          const GdkRectangle   *background_area,
                                          const GdkRectangle   *cell_area,
                                          GtkCellRendererState  flags)
{
  xatrace();
  void (*func) (GtkWidget            *widget,
                GtkCellRenderer      *cellr,
                cairo_t              *cr,
                GtkWidget            *treeview,
                const GdkRectangle   *background_area,
                const GdkRectangle   *cell_area,
                GtkCellRendererState  flags) = NULL;

  if (! widget) {
    printf ("No widget\n");
    return;
  }

  if (gtk_widget_get_ancestor (widget, GTK_TYPE_LABEL) == widget) {
    printf ("label\n");
    func = gtk_cell_renderer_text_render_redux;
  } else if (gtk_widget_get_ancestor (widget, GTK_TYPE_SPINNER) == widget) {
    printf ("spinner\n");
    func = gtk_cell_renderer_spinner_render_redux;
  } else if (gtk_widget_get_ancestor (widget, GTK_TYPE_PROGRESS_BAR) == widget) {
    printf ("progress\n");
    func = gtk_cell_renderer_progress_render_redux;
/*  } else if ((gtk_widget_get_ancestor (widget, GTK_TYPE_IMAGE) == widget))
    func = gtk_cell_rendrer_pixbuf_render_redux;*/
  }

  if (func) {
    return func (widget, cellr, cr, treeview, background_area, cell_area, flags);
  }

  if ((gtk_widget_get_ancestor (widget, GTK_TYPE_CONTAINER) == widget)) {
    GList *l = gtk_container_get_children (GTK_CONTAINER(widget));
    printf ("container: %p\n", l);
    while ((l = g_list_next(l)) != NULL) {
      gtk_cell_renderer_widget_render_internal (l->data, cellr, cr, treeview, background_area,
                                                cell_area, flags);
    }
    return;
  }

  printf ("INVALID\n");
  G_OBJECT_WARN_INVALID_PROPERTY_ID (widget, 0, NULL);
  return;
}

void xabreak(void) {};

static void
gtk_cell_renderer_widget_render (GtkCellRenderer      *cellr,
                                  cairo_t              *cr,
                                  GtkWidget            *treeview,
                                  const GdkRectangle   *background_area,
                                  const GdkRectangle   *cell_area,
                                  GtkCellRendererState  flags)
{
  xatrace();  GtkCellRendererWidget *cell = GTK_CELL_RENDERER_WIDGET (cellr);
  GtkCellRendererWidgetPrivate *priv = cell->priv;
  GtkWidget *widget = priv->widget;
  GtkAllocation *alloc = (GtkAllocation *) cell_area;

  if (!widget)
    return;

  gtk_widget_show (widget);
  gtk_widget_size_allocate (widget, alloc);
  gtk_widget_draw (widget, cr);

  xabreak();

  return gtk_cell_renderer_widget_render_internal (widget,
                 cellr, cr, treeview, background_area, cell_area, flags);
}

void treestore_set_widget(GtkTreeStore * tstore, GtkTreeIter * iter,
                           const char * label, GtkWidget * widget)
{
  xatrace();   gtk_tree_store_set(tstore, iter, 0, label, 1, FALSE, 3, TRUE, 4, TRUE,
                      5, widget, -1);
  printf ("widget is: %p\n", widget);
   //   gtk_object_sink(GTK_OBJECT(widget));
}

GtkBox *make_box ()
{
  GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
  GtkWidget *label = gtk_label_new ("embeded label test");
  GtkWidget *image = gtk_image_new_from_stock (GTK_STOCK_NEW, GTK_ICON_SIZE_DIALOG);
  GtkWidget *spinner = gtk_spinner_new ();
  gtk_spinner_start (GTK_SPINNER(spinner));

  gtk_box_pack_start (GTK_BOX(box), GTK_WIDGET(image),   FALSE, FALSE, 0);
  gtk_box_pack_start (GTK_BOX(box), GTK_WIDGET(spinner), FALSE, FALSE, 0);
  gtk_box_pack_start (GTK_BOX(box), GTK_WIDGET(label),   FALSE, FALSE, 0);

  return GTK_BOX(box);
}

void test_treeview(GtkScrolledWindow * sw)
{
  xatrace();	GtkCellRenderer * r2;

	GtkSpinner *the_spinner = GTK_SPINNER(gtk_spinner_new());
  GtkLabel   *the_label   = GTK_LABEL  (gtk_label_new("test label"));
  GtkBox     *the_box     = make_box();
   /*gtk_widget_show(GTK_WIDGET(the_spinner));*/
   printf("new the_spinner = %p\n", the_spinner);
   /*   g_signal_connect(G_OBJECT(the_spinner), "destroy",
                    G_CALLBACK(the_spinner_destroyed), 0);
   g_signal_connect(G_OBJECT(the_spinner), "expose-event",
                    G_CALLBACK(the_spinner_is_exposed), 0);
   */
   GtkTreeStore * tstore = gtk_tree_store_new(6,
                           G_TYPE_STRING,  /* label */
                           G_TYPE_BOOLEAN, /* is_separator */
                           G_TYPE_STRING,  /* contents */
                           G_TYPE_BOOLEAN, /* contents.visible */
                           G_TYPE_BOOLEAN, /* contents.editable */
                           G_TYPE_OBJECT   /* contents.widget */);
   GtkWidget * treeview = gtk_tree_view_new_with_model(GTK_TREE_MODEL(tstore));
   /*   g_signal_connect(G_OBJECT(treeview), "expose-event",
                    G_CALLBACK(treeview_expose_model_widgets), 0);
   */
   /*
   gtk_tree_view_set_row_separator_func(GTK_TREE_VIEW(treeview),
                                        is_treeview_row_a_separator, 0, 0);
   */

   GtkCellRenderer * r1 = gtk_cell_renderer_text_new();
   GtkTreeViewColumn * col1 = gtk_tree_view_column_new_with_attributes(
                              "Label", r1, "text", 0, NULL);
   gtk_tree_view_append_column(GTK_TREE_VIEW(treeview), col1);

   r2 = gtk_cell_renderer_widget_new();
   GtkTreeViewColumn * col2 = gtk_tree_view_column_new_with_attributes(
                              "Contents", r2, "widget", 5, NULL);
   gtk_tree_view_append_column(GTK_TREE_VIEW(treeview), col2);

   gtk_tree_view_set_rules_hint(GTK_TREE_VIEW(treeview), TRUE);
   gtk_tree_view_set_headers_visible(GTK_TREE_VIEW(treeview), FALSE);
   gtk_container_add(GTK_CONTAINER(sw), treeview);

   GtkTreeIter pi, ci, gi;
   gtk_tree_store_append(tstore, &pi, 0);
   gtk_tree_store_set(tstore, &pi, 0, "Parent 1", 1, FALSE,
                      2, "Value 1", 3, FALSE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 1.1", 1, FALSE,
                      2, "Value 1.1", 3, TRUE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 1.2", 1, FALSE,
                      2, "Value 1.2", 3, TRUE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 1.3", 1, FALSE,
                      2, "Value 1.3", 3, TRUE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &pi, 0);
   gtk_tree_store_set(tstore, &pi, 0, "Parent 2", 1, FALSE,
                      2, "Value 2", 3, FALSE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 2.1", 1, FALSE,
                      2, "Value 2.1", 3, FALSE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &gi, &ci);
   gtk_tree_store_set(tstore, &gi, 0, "Grandchild 2.1.1", 1, FALSE,
                      2, "Value 2.1.1", 3, FALSE, 4, TRUE, -1); //5, GTK_WIDGET(the_label), -1);

   gtk_tree_store_append(tstore, &gi, &ci);
   gtk_tree_store_set(tstore, &gi, 0, "Grandchild 2.1.2", 1, FALSE,
                        2, "Value 2.1.2", 3, TRUE, 4, TRUE, -1); //5, GTK_WIDGET(the_spinner) -1);

   gtk_tree_store_append(tstore, &gi, &ci);
   gtk_tree_store_set(tstore, &gi, 0, "Grandchild 2.1.3", 1, FALSE,
                      2, "Value 2.1.3", 3, TRUE, 4, TRUE, 5, GTK_WIDGET(the_box), -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 2.2", 1, FALSE,
                      2, "Value 2.2", 3, TRUE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 2.3", 1, FALSE,
                      2, "Value 2.3", 3, TRUE, 4, TRUE, -1);

   gtk_tree_view_expand_row(GTK_TREE_VIEW(treeview),
                            gtk_tree_model_get_path(GTK_TREE_MODEL(tstore), &pi),
                            TRUE /*open_all*/);

   gtk_tree_store_append(tstore, &pi, 0);
   gtk_tree_store_set(tstore, &pi, 0, "Separator", 1, TRUE,
                      2, "(separator)", 3, FALSE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &pi, 0);
   gtk_tree_store_set(tstore, &pi, 0, "Parent 3", 1, FALSE,
                      2, "Value 3", 3, FALSE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 3.1", 1, FALSE,
                      2, "Value 3.1", 3, TRUE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 3.2", 1, FALSE,
                      2, "Value 3.2", 3, TRUE, 4, TRUE, -1);

   gtk_tree_store_append(tstore, &ci, &pi);
   gtk_tree_store_set(tstore, &ci, 0, "Child 3.3", 1, FALSE,
                      2, "Value 3.3", 3, TRUE, 4, TRUE, -1);

   g_object_unref(G_OBJECT(tstore));
}

GType gtk_cell_renderer_widget_register_type()
{
  xatrace();   static const GTypeInfo renderer_widget_info =
   {
     sizeof(struct _GtkCellRendererWidgetClass),
     0,    /* base_init */
     0,    /* base_finalize */
     (GClassInitFunc) gtk_cell_renderer_widget_class_init,
     0,    /* class_finalize */
     0,    /* class_data */
     sizeof(GtkCellRendererWidget),
     0,    /* n_preallocs */
     (GInstanceInitFunc) gtk_cell_renderer_widget_init,
   };
   return g_type_register_static(GTK_TYPE_CELL_RENDERER,
                                 "xaGtkCellRendererWidget",
                                 &renderer_widget_info, 0);
}

int main(int argc, char ** argv)
{
  xatrace();
   gtk_init(&argc, &argv);
//   GtkCellRendererWidget *cell_renderer_widget_type = GTK_CELL_RENDERER_WIDGET(gtk_cell_renderer_widget_register_type());

   GtkWidget * window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
   gtk_window_set_default_size(GTK_WINDOW(window), 500, 300);
   g_signal_connect(G_OBJECT(window), "destroy", G_CALLBACK(gtk_main_quit), 0);
   g_signal_connect(G_OBJECT(window), "delete_event", G_CALLBACK(gtk_main_quit),
                    0);
   GtkWidget * sw = gtk_scrolled_window_new(0, 0);
   test_treeview(GTK_SCROLLED_WINDOW(sw));
   gtk_container_add(GTK_CONTAINER(window), sw);
   gtk_widget_show_all(window);

   gtk_main();
   gtk_widget_destroy(sw);
   return 0;
}
