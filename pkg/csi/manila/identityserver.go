/*
Copyright 2019 The Kubernetes Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package manila

import (
	"context"

	"github.com/container-storage-interface/spec/lib/go/csi"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"k8s.io/klog/v2"
)

type identityServer struct {
	d *Driver
}

func (ids *identityServer) GetPluginInfo(ctx context.Context, req *csi.GetPluginInfoRequest) (*csi.GetPluginInfoResponse, error) {
	klog.V(5).Infof("Using default GetPluginInfo")

	if ids.d.name == "" {
		return nil, status.Error(codes.Unavailable, "Driver name not configured")
	}

	if ids.d.fqVersion == "" {
		return nil, status.Error(codes.Unavailable, "Driver is missing version")
	}

	return &csi.GetPluginInfoResponse{
		Name:          ids.d.name,
		VendorVersion: ids.d.fqVersion,
	}, nil
}

func (ids *identityServer) Probe(ctx context.Context, req *csi.ProbeRequest) (*csi.ProbeResponse, error) {
	csiConn, err := ids.d.csiClientBuilder.NewConnectionWithContext(ctx, ids.d.fwdEndpoint)
	if err != nil {
		return nil, status.Error(codes.FailedPrecondition, fmtGrpcConnError(ids.d.fwdEndpoint, err))
	}
	defer csiConn.Close()

	return ids.d.csiClientBuilder.NewIdentityServiceClient(csiConn).Probe(ctx, req)
}

func (ids *identityServer) GetPluginCapabilities(ctx context.Context, req *csi.GetPluginCapabilitiesRequest) (*csi.GetPluginCapabilitiesResponse, error) {
	klog.V(5).Infof("GetPluginCapabilities called with req %+v", req)
	caps := []*csi.PluginCapability{
		{
			Type: &csi.PluginCapability_Service_{
				Service: &csi.PluginCapability_Service{
					Type: csi.PluginCapability_Service_CONTROLLER_SERVICE,
				},
			},
		},
		{
			Type: &csi.PluginCapability_VolumeExpansion_{
				VolumeExpansion: &csi.PluginCapability_VolumeExpansion{
					Type: csi.PluginCapability_VolumeExpansion_ONLINE,
				},
			},
		},
	}

	if ids.d.withTopology {
		caps = append(caps, &csi.PluginCapability{
			Type: &csi.PluginCapability_Service_{
				Service: &csi.PluginCapability_Service{
					Type: csi.PluginCapability_Service_VOLUME_ACCESSIBILITY_CONSTRAINTS,
				},
			},
		})
	}

	return &csi.GetPluginCapabilitiesResponse{
		Capabilities: caps,
	}, nil
}
