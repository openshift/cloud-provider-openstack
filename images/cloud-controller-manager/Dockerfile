FROM registry.ci.openshift.org/ocp/builder:rhel-9-golang-1.25-openshift-4.22
WORKDIR /go/src/k8s.io/cloud-provider-openstack
COPY . .
RUN go build -o openstack-cloud-controller-manager ./cmd/openstack-cloud-controller-manager

FROM registry.ci.openshift.org/ocp/4.22:base-rhel9

COPY --from=0 /go/src/k8s.io/cloud-provider-openstack/openstack-cloud-controller-manager /usr/bin/

ENTRYPOINT ["/usr/bin/openstack-cloud-controller-manager"]
