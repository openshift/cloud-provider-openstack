FROM registry.ci.openshift.org/ocp/builder:rhel-9-golang-1.24-openshift-4.20
WORKDIR /go/src/k8s.io/cloud-provider-openstack
COPY . .
RUN go build -o manila-csi-plugin ./cmd/manila-csi-plugin

FROM registry.ci.openshift.org/ocp/4.20:base-rhel9

COPY --from=0 /go/src/k8s.io/cloud-provider-openstack/manila-csi-plugin /usr/bin/

ENTRYPOINT ["/usr/bin/manila-csi-plugin"]
