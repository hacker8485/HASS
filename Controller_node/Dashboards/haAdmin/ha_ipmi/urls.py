from django.conf.urls import patterns
from django.conf.urls import url
from openstack_dashboard.dashboards.haAdmin.ha_ipmi.views \
    import DetailView
from openstack_dashboard.dashboards.haAdmin.ha_ipmi.views \
    import IndexView

# from openstack_dashboard.dashboards.haAdmin.ha_ipmi.views \
#    import UpdateView
# from openstack_dashboard.dashboards.haAdmin.ha_ipmi.views \
#    import AddView

urlpatterns = patterns(
    '',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<node_id>[^/]+)/$',
        DetailView.as_view(), name='detail'),
    # url(r'^add_to_protection/$', AddView.as_view(), name='add_to_protection'),
    # url(INSTANCES % 'update',
    # UpdateView.as_view(),
    # name='update'),
)
