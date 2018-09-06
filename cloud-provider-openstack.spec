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

%global golang_version 1.8.1
%{!?version: %global version 0.2.0}
%{!?release: %global release 1}
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
%if 0%{do_prep}
%setup -q
%endif

%build
%if 0%{do_build}
%if 0%{make_redistributable}
# Create Binaries for all internally defined arches
%{os_git_vars} make manila-provisioner
%else
# Create Binaries only for building arch
%ifarch x86_64
  BUILD_PLATFORM="linux/amd64"
%endif
%ifarch %{ix86}
  BUILD_PLATFORM="linux/386"
%endif
%ifarch ppc64le
  BUILD_PLATFORM="linux/ppc64le"
%endif
%ifarch %{arm} aarch64
  BUILD_PLATFORM="linux/arm64"
%endif
%ifarch s390x
  BUILD_PLATFORM="linux/s390x"
%endif
OS_ONLY_BUILD_PLATFORMS="${BUILD_PLATFORM}" %{os_git_vars} make manila-provisioner
%endif
%endif

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
* Thu Aug 23 2018 Tomas Smetana <tsmetana@redhat.com> 0.2.0-1
- Initial package: Manila provisioner subpackage only
