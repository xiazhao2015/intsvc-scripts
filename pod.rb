# 第一版 code:  

+# setup tier_down to restore docker-registry and router pods after scenario end;
+Given /^The registry and router pods are restored after scenario$/ do
+  ensure_admin_tagged
+
+  @result = admin.cli_exec(:get, resource: 'pods', o: 'yaml')
+  if @result[:success]
+    orig_pods = @result[:response]
+    logger.info "Registry and router pods restore tear_down registered:\n#{orig_pods}"
+  else
+    raise "could not get pods"
+  end
+
+  _admin = admin
+  teardown_add {
+    admin.cli_exec(
+      :delete,
+      object_type: :pods,
+      all: ""
+    )
+    # we don't check result here, we don't care if it existed or not
+    # we care if it will be created successfully below
+
+    @result = _admin.cli_exec(
+      :create,
+      f: "-",
+      _stdin: orig_pods
+    )
+    raise "cannot restore registry and router pods" unless @result[:success]
+  }
+end


# 第二版 code:
 +# setup tier_down to restore docker-registry pods after scenario end;
+Given /^the default registry replication count is restored after scenario$/ do
+  ensure_admin_tagged
+
+  @result = admin.cli_exec(:get, resource: 'deploymentConfigs', resource_name: 'docker-registry', o: 'yaml')
+  if @result[:success]
+    orig_dc= @result[:response]
+    logger.info "Registry pods restore tear_down registered:\n#{orig_dc}"
+  else
+    raise "could not get registry deploymentconfig"
+  end
+
+  _admin = admin
+  teardown_add {
+    @result = _admin.cli_exec(
+      :replace,
+      f: "-",
+      _stdin: orig_dc
+    )
+    raise "cannot restore registry pods" unless @result[:success]
+    step %Q/I wait until replicationController "docker-registry-5" is ready/
+  }
+end
+
+# setup tier_down to restore router pods after scenario end;
+Given /^the default router replication count is restored after scenario$/ do
+  ensure_admin_tagged
+
+  @result = admin.cli_exec(:get, resource: 'deploymentConfigs', resource_name: 'router', o: 'yaml')
+  if @result[:success]
+    orig_dc= @result[:response]
+    logger.info "Router pods restore tear_down registered:\n#{orig_dc}"
+  else
+    raise "could not get router deploymentconfig"
+  end
+
+  _admin = admin
+  teardown_add {
+    @result = _admin.cli_exec(
+      :replace,
+      f: "-",
+      _stdin: orig_dc
+    )
+    raise "cannot restore router pods" unless @result[:success]
+    step %Q/I wait until replicationController "router-4" is ready/
