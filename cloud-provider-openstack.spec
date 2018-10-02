#debuginfo not supported with Go
%global debug_package %{nil}

# modifying the Go binaries breaks the DWARF debugging
%global __os_install_post %{_rpmconfigdir}/brp-compress

# %commit and %os_git_vars are intended to be set by tito custom builders provided
# in the .tito/lib directory. The values in this spec file will not be kept up to date.
%{!?commit: %global commit HEAD }
%global shortcommit %(c=%{commit}; echo ${c:0:7})
# os_git_vars needed to run hack scripts during rpm builds
%{!?os_git_vars: %global os_git_vars OS_GIT_VERSION='' OS_GIT_COMMIT='' OS_GIT_MAJOR='' OS_GIT_MINOR='' OS_GIT_TREE_STATE='' }

%if 0%{?skip_build}
%global do_build 0
%else
%global do_build 1
%endif
%if 0%{?skip_prep}
%global do_prep 0
%else
%global do_prep 1
%endif

%if 0%{?fedora} || 0%{?epel}
%global need_redistributable_set 0
%else
# Due to library availability, redistributable builds only work on x86_64
%ifarch x86_64
%global need_redistributable_set 1
%else
%global need_redistributable_set 0
%endif
%endif
%{!?make_redistributable: %global make_redistributable %{need_redistributable_set}}

#
# Customize from here.
#
%if ! 0%{?gobuild:1}
%define gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**};
%endif

%global provider        k8s
%global provider_tld    io
%global project         kubernetes
%global repo            cloud-provider-openstack
# https://k8s.io/kubernetes/cloud-provider-openstack
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}

%global golang_version 1.8.1
%{!?version: %global version 0.2.0}
%{!?release: %global release 2}
%global package_name cloud-provider-openstack
%global product_name TODO #
%global import_path github.com/openshift/cloud-provider-openstack

Name:           %{package_name}
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        Implementation of external cloud provider for OpenStack clusters
License:        ASL 2.0
URL:            https://%{import_path}
Source0:        https://%{import_path}/archive/v%{version}/%{name}-%{version}.tar.gz
BuildRequires:  golang >= %{golang_version}

# If go_arches not defined fall through to implicit golang archs
%if 0%{?go_arches:1}
ExclusiveArch:  %{go_arches}
%else
ExclusiveArch:  x86_64 aarch64 ppc64le s390x
%endif

### AUTO-BUNDLED-GEN-ENTRY-POINT

%description
Implementation of external cloud provider for OpenStack clusters. An external cloud provider is a kubernetes
controller that runs cloud provider-specific loops required for the functioning of kubernetes.

%package -n atomic-openshift-manila-provisioner
Summary: Provisioner for OpenStack Manila

%description -n atomic-openshift-manila-provisioner
Provisions volumes using OpenStack Manila API.

%prep
# cloud-provider-openstack assumes it's compiled in a Go workspace
# Let's create one
%if 0%{do_prep}
%setup -q -n %{name}
%endif

%build
export GOPATH=$(pwd):$(pwd)/vendor:%{gopath}
mkdir -p src/%{provider}.%{provider_tld}
ln -s ../../../%{name} src/%{provider}.%{provider_tld}/
cd src/%{provider}.%{provider_tld}/%{name}
%gobuild -o manila-provisioner cmd/manila-provisioner/main.go

%install

PLATFORM="$(go env GOHOSTOS)/$(go env GOHOSTARCH)"
install -d %{buildroot}%{_bindir}

# Install linux components
for bin in manila-provisioner
do
  install -p -m 755 ${bin} %{buildroot}%{_bindir}/${bin}
done

%files

%files -n atomic-openshift-manila-provisioner
%license LICENSE
%{_bindir}/manila-provisioner

%files

%changelog
* Tue Sep 18 2018 Tomas Smetana <tsmetana@redhat.com> 0.2.0-2
- Create complete Go workspace for the build

* Thu Aug 23 2018 Tomas Smetana <tsmetana@redhat.com> 0.2.0-1
- Initial package: Manila provisioner subpackage only
