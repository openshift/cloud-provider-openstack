FROM openshift/origin-base

RUN INSTALL_PKGS="atomic-openshift-manila-provisioner" && \
    yum --enablerepo=origin-local-release install -y ${INSTALL_PKGS} && \
    rpm -V ${INSTALL_PKGS} && \
    yum clean all

LABEL io.k8s.display-name="OpenShift Manila provisioner" \
      io.k8s.description="This is a component of OpenShift Container Platform  which allows to provision persistent volumes using OpenStack Manila API." \
io.openshift.tags="openshift,manila,openstack"

ENTRYPOINT ["/usr/bin/manila-provisioner"]
