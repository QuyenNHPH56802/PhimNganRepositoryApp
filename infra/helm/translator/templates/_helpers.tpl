{{- define "translator.deployment" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .name }}
  labels:
    app: translator
    component: {{ .name }}
spec:
  replicas: {{ .replicas }}
  selector:
    matchLabels:
      app: translator
      component: {{ .name }}
  template:
    metadata:
      labels:
        app: translator
        component: {{ .name }}
    spec:
      containers:
        - name: {{ .name }}
          image: "{{ .image.repository }}:{{ .image.tag }}"
          imagePullPolicy: {{ .image.pullPolicy }}
          envFrom:
            - configMapRef:
                name: translator-config
            - secretRef:
                name: translator-secret
          env:
            - name: TRANSLATOR_TASK_QUEUE
              value: {{ .taskQueue | quote }}
          resources:
            {{- toYaml .resources | nindent 12 }}
          readinessProbe:
            exec:
              command: ["sh", "-c", "exit 0"]
            initialDelaySeconds: 5
            periodSeconds: 10
      {{- with .nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
{{- end }}