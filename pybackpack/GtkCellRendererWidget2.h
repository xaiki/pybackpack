
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
#if !defined (__GTK_H_INSIDE__) && !defined (GTK_COMPILATION)
#error "Only <gtk/gtk.h> can be included directly."
#endif
*/
#ifndef __GTK_CELL_RENDERER_WIDGET_H__
#define __GTK_CELL_RENDERER_WIDGET_H__

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define GTK_TYPE_CELL_RENDERER_WIDGET            (gtk_cell_renderer_widget_get_type ())
#define GTK_CELL_RENDERER_WIDGET(obj)            (G_TYPE_CHECK_INSTANCE_CAST ((obj), GTK_TYPE_CELL_RENDERER_WIDGET, GtkCellRendererWidget))
#define GTK_CELL_RENDERER_WIDGET_CLASS(klass)    (G_TYPE_CHECK_CLASS_CAST ((klass), GTK_TYPE_CELL_RENDERER_WIDGET, GtkCellRendererWidgetClass))
#define GTK_IS_CELL_RENDERER_WIDGET(obj)         (G_TYPE_CHECK_INSTANCE_TYPE ((obj), GTK_TYPE_CELL_RENDERER_WIDGET))
#define GTK_IS_CELL_RENDERER_WIDGET_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE ((klass), GTK_TYPE_CELL_RENDERER_WIDGET))
#define GTK_CELL_RENDERER_WIDGET_GET_CLASS(obj)  (G_TYPE_INSTANCE_GET_CLASS ((obj), GTK_TYPE_CELL_RENDERER_WIDGET, GtkCellRendererWidgetClass))

typedef struct _GtkCellRendererWidget        GtkCellRendererWidget;
typedef struct _GtkCellRendererWidgetClass   GtkCellRendererWidgetClass;
typedef struct _GtkCellRendererWidgetPrivate GtkCellRendererWidgetPrivate;

struct _GtkCellRendererWidget
{
  GtkCellRendererText                parent;

  /*< private >*/
  GtkCellRendererWidgetPrivate *priv;
};

struct _GtkCellRendererWidgetClass
{
  GtkCellRendererTextClass parent_class;

  /* Padding for future expansion */
  void (*_gtk_reserved1) (void);
  void (*_gtk_reserved2) (void);
  void (*_gtk_reserved3) (void);
  void (*_gtk_reserved4) (void);
};

GType            gtk_cell_renderer_widget_get_type (void) G_GNUC_CONST;
GtkCellRenderer *gtk_cell_renderer_widget_new      (void);

G_END_DECLS

#endif /* __GTK_CELL_RENDERER_WIDGET_H__ */
