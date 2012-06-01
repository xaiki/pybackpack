#include <gtk/gtk.h>
#include <xtk/gtkcellrendererwidget.h>

void treestore_set_widget(GtkTreeStore * tstore, GtkTreeIter * iter,
                           const char * label, GtkWidget * widget)
{
 gtk_tree_store_set(tstore, iter, 0, label, 1, FALSE, 3, TRUE, 4, TRUE,
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

  gtk_widget_set_hexpand (box, TRUE);
  return GTK_BOX(box);
}

void test_treeview(GtkScrolledWindow * sw)
{
	GtkCellRenderer * r2;

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

   r2 = xtk_cell_renderer_widget_new();
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

int main(int argc, char ** argv)
{
   gtk_init(&argc, &argv);
//   GtkCellRendererWidget *cell_renderer_widget_type = XTK_CELL_RENDERER_WIDGET(xtk_cell_renderer_widget_register_type());

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
