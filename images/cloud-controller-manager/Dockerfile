FROM registry.ci.openshift.org/ocp/builder:rhel-9-golang-1.24-openshift-4.20
WORKDIR /go/src/k8s.io/cloud-provider-openstack
COPY . .
RUN go build -o openstack-cloud-controller-manager ./cmd/openstack-cloud-controller-manager

FROM registry.ci.openshift.org/ocp/4.20:base-rhel9

COPY --from=0 /go/src/k8s.io/cloud-provider-openstack/openstack-cloud-controller-manager /usr/bin/

ENTRYPOINT ["/usr/bin/openstack-cloud-controller-manager"]
