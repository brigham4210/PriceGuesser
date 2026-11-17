package com.brigham4210.priceguesser;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.view.WindowInsets;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.TextView;
import android.window.OnBackInvokedDispatcher;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends Activity {
    private static final String TAG = "PriceGuesser";
    private static final String LOCAL_HOST = "127.0.0.1";

    private WebView webView;
    private View loading;
    private TextView status;
    private Button retry;
    private String homeUrl;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.web_view);
        loading = findViewById(R.id.loading);
        status = findViewById(R.id.status);
        retry = findViewById(R.id.retry);
        retry.setOnClickListener(v -> startServer());

        applySystemBarInsets(findViewById(R.id.root));

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setSupportMultipleWindows(false);
        webView.setWebViewClient(new GameClient());

        if (Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::handleBack);
        }

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState);
        }
        startServer();
    }

    /** Start Python and the game server off the main thread, then load the game. */
    private void startServer() {
        status.setText(R.string.starting);
        retry.setVisibility(View.GONE);
        loading.setVisibility(View.VISIBLE);
        Handler main = new Handler(Looper.getMainLooper());
        new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }
                int port = Python.getInstance().getModule("android_server")
                        .callAttr("start", getFilesDir().getAbsolutePath()).toInt();
                main.post(() -> onServerReady(port));
            } catch (Throwable err) {
                Log.e(TAG, "Couldn't start the game server", err);
                main.post(this::onServerFailed);
            }
        }, "python-start").start();
    }

    private void onServerReady(int port) {
        homeUrl = "http://" + LOCAL_HOST + ":" + port + "/";
        String current = webView.getUrl();
        if (current == null || !current.startsWith(homeUrl)) {
            webView.loadUrl(homeUrl);
        } else {
            webView.reload();
        }
        loading.setVisibility(View.GONE);
        webView.setVisibility(View.VISIBLE);
    }

    private void onServerFailed() {
        status.setText(R.string.start_failed);
        retry.setVisibility(View.VISIBLE);
    }

    private void handleBack() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            finish();
        }
    }

    @SuppressWarnings("deprecation")
    @Override
    public void onBackPressed() {
        handleBack();
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    @Override
    protected void onDestroy() {
        webView.destroy();
        super.onDestroy();
    }

    /** Keep content clear of the status bar, navigation bar and keyboard (edge-to-edge on Android 15+). */
    @SuppressWarnings("deprecation")
    private static void applySystemBarInsets(View root) {
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            if (Build.VERSION.SDK_INT >= 30) {
                Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
                v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            } else {
                v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                        insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
    }

    /** Game pages stay in the app; Zillow links open in the browser. */
    private class GameClient extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (LOCAL_HOST.equals(uri.getHost())) {
                return false;
            }
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, uri));
            } catch (ActivityNotFoundException err) {
                Log.w(TAG, "No app can open " + uri);
            }
            return true;
        }
    }
}
