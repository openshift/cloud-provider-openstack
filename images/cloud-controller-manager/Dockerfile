FROM registry.ci.openshift.org/ocp/builder:rhel-9-golang-1.26-openshift-5.0
WORKDIR /go/src/k8s.io/cloud-provider-openstack
COPY . .
RUN go build -o openstack-cloud-controller-manager ./cmd/openstack-cloud-controller-manager

FROM registry.ci.openshift.org/ocp/5.0:base-rhel9

COPY --from=0 /go/src/k8s.io/cloud-provider-openstack/openstack-cloud-controller-manager /usr/bin/

ENTRYPOINT ["/usr/bin/openstack-cloud-controller-manager"]
