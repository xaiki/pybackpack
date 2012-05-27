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
  GHashTable *whash;
	GtkWidget *widget;
  GtkWidget *treeview;
	GtkWidget *hack;
  GtkWidget *hackimg;
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

static gboolean
gtk_cell_renderer_widget_cell_draw (GtkWidget *widget,
                                    cairo_t   *cr,
                                    gpointer   user_data)
{
  GtkOffscreenWindow *offscreen = (GtkOffscreenWindow *)user_data;

  printf ("DRAWN\n");
  cairo_set_source_surface (cr,
                            gtk_offscreen_window_get_surface (offscreen),
                            50, 50);
  cairo_paint (cr);

  return FALSE;
}

static gboolean
gtk_cell_renderer_widget_cell_queue_redraw (GtkWidget *window,
                                            GdkEvent  *event,
                                            GtkWidget *treeview)
{
  printf ("DAMAGED\n");
  gtk_widget_queue_draw (treeview);

  return TRUE;
}
/*
static void
gtk_offscreen_window_damaged_cb (GtkWidget *window, GdkEvent *event, GtkWidget *cell)
{

  GtkCellRendererWidgetPrivate *priv = GTK_CELL_RENDERER_WIDGET(cell)->priv;

/*  if (priv->treeview)
    gtk_cell_renderer_widget_cell_queue_redraw (window, event, priv->treeview); * /

  if (! priv->hackimg)
    return;
  GdkPixbuf *p = gtk_offscreen_window_get_pixbuf (GTK_OFFSCREEN_WINDOW(priv->window));

  gtk_image_set_from_pixbuf (GTK_IMAGE (priv->hackimg), p);
}
*/
static void
gtk_cell_renderer_widget_init (GtkCellRendererWidget *cell)
{
  xatrace();

  cell->priv = G_TYPE_INSTANCE_GET_PRIVATE (cell,
                                            GTK_TYPE_CELL_RENDERER_WIDGET,
                                            GtkCellRendererWidgetPrivate);

  cell->priv->whash = g_hash_table_new(NULL, NULL);
/*  g_signal_connect (cell->priv->window, "damage-event",
    G_CALLBACK(gtk_offscreen_window_damaged_cb), cell);*/
  cell->priv->hack = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  g_signal_connect (cell->priv->hack, "destroy", G_CALLBACK (gtk_main_quit), NULL);
  cell->priv->pulse = 0;
  cell->priv->old_icon_size = GTK_ICON_SIZE_INVALID;
  cell->priv->icon_size = GTK_ICON_SIZE_MENU;


}

/**
 * gtk_cell_renderer_widget_new:
 *
 * Returns a new cell renderer which will show a #GtkWidget.
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

static gboolean
gtk_cell_renderer_widget_offscreen_draw (GtkWidget *widget,
                                         cairo_t   *cr,
                                         gpointer  userdata)
{
  cairo_set_source_rgba (cr, 1.0, 1.0, 1.0, 0.0); /* transparent */

  /* draw the background */
  cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
  cairo_paint (cr);

  return FALSE;
}


static void
gtk_cell_renderer_widget_set_property (GObject      *object,
                                        guint         param_id,
                                        const GValue *value,
                                        GParamSpec   *pspec)
{
  xatrace();  GtkCellRendererWidget *cell = GTK_CELL_RENDERER_WIDGET (object);
  GtkCellRendererWidgetPrivate *priv = cell->priv;
  GtkWidget *w;

  switch (param_id)
    {
    case PROP_WIDGET:

      w = g_value_get_object (value);
      if (! w) {
        priv->widget = NULL;
        printf ("widget set to (nil)\n");
        break;
      }
/*      if (w == priv->widget) {
        printf ("widget already set\n");
        break;
        }*/

      priv->widget = w;

      w = g_hash_table_lookup (priv->whash, priv->widget);
      if (!w) {
        w = gtk_offscreen_window_new ();
        g_hash_table_insert (priv->whash, priv->widget, w);
        gtk_container_add (GTK_CONTAINER (w), priv->widget);
        gtk_widget_set_app_paintable (w, TRUE);

        g_signal_connect (G_OBJECT(w), "draw",
                          G_CALLBACK (gtk_cell_renderer_widget_offscreen_draw),
                          NULL);
        gtk_widget_show_all (w);
      }

      printf ("%p:%p, setting widget to: %p, on window: %p\n", object, priv, priv->widget, w);
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

  if (x_offset)
    *x_offset = 0;
  if (y_offset)
    *y_offset = 0;

  if (! priv->widget) {
    if (width)
      *width = 0;
    if (height)
      *height = 0;
    return;
  }

  GtkRequisition natural_size;
  GtkRequisition min;

  gtk_widget_get_preferred_size (priv->widget, &min, &natural_size);
  printf ("requesting: %dx%d\n", natural_size.width, natural_size.height);
  printf ("requesting (min): %dx%d\n", min.width, min.height);
  if (width)
    *width = natural_size.width;
  if (height)
    *height = natural_size.height;

  return;
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

void xabreak(void) {};

inline static GtkWidget *
get_first_child (GtkWidget *p)
{
  return p==NULL?NULL:GTK_WIDGET(gtk_container_get_children (GTK_CONTAINER(p))->data);
}

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
  GtkWidget *window;
  GtkAllocation *alloc = (GtkAllocation *) cell_area;
  GtkStyleContext *context = gtk_widget_get_style_context (treeview);

  GdkRectangle pix_rect;
  GdkRectangle draw_rect;
  gint xpad, ypad;

  int ahah = 0;

  cairo_surface_t *cs = NULL;

  if (!widget)
    return;

  window = g_hash_table_lookup (priv->whash, widget);
  if (! window) {
	  printf ("No WINDOW for %p !!! how can this happen ?!!?\n", widget);
	  return;
  }

  priv->treeview = treeview;
  gtk_cell_renderer_widget_get_size (cellr, treeview, (GdkRectangle *) cell_area,
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

  if (!gdk_rectangle_intersect (cell_area, &pix_rect, &draw_rect)) {
    printf ("nothing to draw, no intersection\n");
    return;
  }

  cs = gtk_offscreen_window_get_surface (GTK_OFFSCREEN_WINDOW(window));

  gtk_widget_show_all (priv->hack);
  cairo_save (cr);

  gdk_cairo_rectangle (cr, cell_area);
  cairo_clip (cr);

  cairo_set_source_surface (cr, cs, draw_rect.x, draw_rect.y);
  printf (" +++  painting on: %p:%dx%d, with surface: %p\n", cr, draw_rect.x, draw_rect.y, cs);

  cairo_paint (cr);
  cairo_restore (cr);
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
  GtkWidget *button = gtk_button_new_with_mnemonic ("Test Embeded Button");
  gtk_spinner_start (GTK_SPINNER(spinner));

  gtk_box_pack_start (GTK_BOX(box), GTK_WIDGET(image),   TRUE, TRUE, 0);
  gtk_box_pack_start (GTK_BOX(box), GTK_WIDGET(spinner), TRUE, TRUE, 0);
  gtk_box_pack_start (GTK_BOX(box), GTK_WIDGET(label),   TRUE, TRUE, 0);
  gtk_box_pack_start (GTK_BOX(box), GTK_WIDGET(button),  TRUE, TRUE, 0);

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
   printf("new the_label = %p\n", the_label);
   printf("new the_box = %p\n", the_box);
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
                      2, "Value 2.1.1", 3, FALSE, 4, TRUE, 5, GTK_WIDGET(the_label), -1);

   gtk_tree_store_append(tstore, &gi, &ci);
   gtk_tree_store_set(tstore, &gi, 0, "Grandchild 2.1.2", 1, FALSE,
                      2, "Value 2.1.2", 3, TRUE, 4, TRUE, 5, GTK_WIDGET(the_spinner), -1);

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
