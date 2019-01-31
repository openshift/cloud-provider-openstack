FROM registry.svc.ci.openshift.org/openshift/release:golang-1.10 AS builder
WORKDIR /go/src/k8s.io/cloud-provider-openstack
COPY . .
RUN go build -o manila-provisioner cmd/manila-provisioner/main.go

FROM registry.svc.ci.openshift.org/openshift/origin-v3.11:base
COPY --from=builder /go/src/k8s.io/cloud-provider-openstack/manila-provisioner /

ENTRYPOINT ["/manila-provisioner"]
LABEL io.k8s.display-name="OpenShift Manila provisioner" \
      io.k8s.description="This is a component of OpenShift Container Platform  which allows to provision persistent volumes using OpenStack Manila API." \
      io.openshift.tags="openshift,manila,openstack"
