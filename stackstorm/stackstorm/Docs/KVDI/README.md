# KVDI - A Virtual Desktop Infrastructure running on Kubernetes
Installation:

1. Install helm

2. Add the kvdi helm chart:
  `helm repo remove tinyzimmer`
  `helm repo add kvdi https://kvdi.github.io/kvdi/deploy/charts`
  `helm repo update`

3. Install kvdi using helm:
  `helm install kvdi kvdi/kvdi`

Once installed, you can retrieve the initial admin password by getting `kvdi-admin-secret` and converting it from base64
`kubectl get secret kvdi-admin-secret --output yaml`

The app service is called `kvdi-app` - you can retrieve the endpoint with:
`kubectl get svc kvdi-app`

With minikube, you can get the ip with: `minikube ip`

To access the Web UI the url is: `http://<minikube-ip>:<kvdi-app_tcp_port>`
http://192.168.49.2:31720


# Building kVDI Desktops
To build a new desktop image, some examples are provided in the kvdi repo
https://github.com/kvdi/kvdi/tree/main/build/desktops

In general, each desktop image requires a VNC server for graphical desktop
sharing.

Note: there is an issue with using Openstack Magnum related to this dispaly.sock
KVDI will repeatedly try to connect with the display server but will be given `permission denied`

`Failed to connect to display server {"error": "dial unix /var/run/kvdi/display.sock: connect: permission denied"}`

You will need to define a KVDI desktop template in order to run KVDI Desktop.
See the Geant4 and Ubuntu-xfce4 templates for reference
