package ch.animalhealth.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.net.Uri;
import android.os.Bundle;
import android.provider.MediaStore;
import android.webkit.JavascriptInterface;
import android.webkit.MimeTypeMap;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public final class MainActivity extends Activity {
    private static final int FILE_CHOOSER_REQUEST = 9002;
    private static final int EXPORT_REQUEST = 9003;
    private StandaloneBackend backend;
    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private Uri pendingCameraUri;
    private byte[] pendingExportBytes;
    private String pendingExportMime;
    private String pendingExportName;

    @Override
    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        backend = new StandaloneBackend(this);
        getWindow().setStatusBarColor(Color.WHITE);
        getWindow().getDecorView().setSystemUiVisibility(android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        webView.setBackgroundColor(Color.rgb(250, 250, 250));
        webView.addJavascriptInterface(new AndroidBridge(), "AndroidBridge");
        webView.setWebChromeClient(new SharedUiChromeClient());
        webView.setWebViewClient(new SharedUiWebViewClient());
        setContentView(webView);
        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.removeJavascriptInterface("AndroidBridge");
            webView.destroy();
        }
        if (backend != null) backend.close();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    private final class AndroidBridge {
        @JavascriptInterface
        public String call(String json) {
            try {
                JSONObject request = new JSONObject(json == null ? "{}" : json);
                String type = request.optString("type", "");
                if ("animal_health/v0817/medications/record".equals(type) && request.has("items")) {
                    request.put("type", "animal_health/v0817/medications/batch_record");
                } else if ("animal_health/v0817/medication/save".equals(type)) {
                    request.put("type", "animal_health/v0817/medications/record");
                }
                if ("animal_health/groups/lifecycle".equals(type)) return lifecycleState().toString();
                if ("animal_health/groups/archive".equals(type)) {
                    setGroupArchived(request.getString("group_id"), true);
                    return new JSONObject().put("group_id", request.getString("group_id")).put("archived_at", Instant.now().toString()).toString();
                }
                if ("animal_health/groups/restore".equals(type)) {
                    setGroupArchived(request.getString("group_id"), false);
                    return new JSONObject().put("group_id", request.getString("group_id")).toString();
                }
                String result = backend.handle(request.toString());
                if ("animal_health/groups/delete".equals(type)) setGroupArchived(request.optString("group_id"), false);
                return result;
            } catch (Exception error) {
                try { return new JSONObject().put("__error", error.getMessage() == null ? error.toString() : error.getMessage()).toString(); }
                catch (Exception ignored) { return "{\"__error\":\"Android bridge error\"}"; }
            }
        }

        @JavascriptInterface
        public void toast(String message, boolean bad) {
            runOnUiThread(() -> Toast.makeText(MainActivity.this, message, bad ? Toast.LENGTH_LONG : Toast.LENGTH_SHORT).show());
        }

        @JavascriptInterface
        public void exportData(String kind, String resourceId) {
            runOnUiThread(() -> prepareExport(kind, resourceId));
        }
    }

    private JSONObject lifecycleState() throws Exception {
        SharedPreferences prefs = getSharedPreferences("animal_health_android", MODE_PRIVATE);
        String stored = prefs.getString("archived_groups", "{}");
        return new JSONObject().put("archived", new JSONObject(stored == null ? "{}" : stored));
    }

    private void setGroupArchived(String groupId, boolean archived) throws Exception {
        if (groupId == null || groupId.isBlank()) return;
        SharedPreferences prefs = getSharedPreferences("animal_health_android", MODE_PRIVATE);
        JSONObject state = lifecycleState().getJSONObject("archived");
        if (archived) state.put(groupId, Instant.now().toString()); else state.remove(groupId);
        prefs.edit().putString("archived_groups", state.toString()).apply();
    }

    private final class SharedUiChromeClient extends WebChromeClient {
        @Override
        public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
            if (fileCallback != null) fileCallback.onReceiveValue(null);
            fileCallback = callback;
            Intent content = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            content.addCategory(Intent.CATEGORY_OPENABLE);
            content.setType("*/*");
            content.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, params != null && params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE);
            List<Intent> initial = new ArrayList<>();
            try {
                ContentValues values = new ContentValues();
                values.put(MediaStore.Images.Media.DISPLAY_NAME, "animal-health-" + System.currentTimeMillis() + ".jpg");
                values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
                pendingCameraUri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
                if (pendingCameraUri != null) {
                    Intent camera = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                    camera.putExtra(MediaStore.EXTRA_OUTPUT, pendingCameraUri);
                    camera.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    if (camera.resolveActivity(getPackageManager()) != null) initial.add(camera);
                }
            } catch (Exception ignored) { pendingCameraUri = null; }
            Intent chooser = Intent.createChooser(content, "Foto oder Datei auswählen");
            if (!initial.isEmpty()) chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, initial.toArray(new Intent[0]));
            startActivityForResult(chooser, FILE_CHOOSER_REQUEST);
            return true;
        }
    }

    private final class SharedUiWebViewClient extends WebViewClient {
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            String path = uri.getPath() == null ? "" : uri.getPath();
            try {
                if (path.contains("/api/animal_health/frontend/animal-health-brand.png")) {
                    InputStream input = getAssets().open("animal-health-brand.svg");
                    return new WebResourceResponse("image/svg+xml", "UTF-8", input);
                }
                if ("app.local".equals(uri.getHost()) && path.startsWith("/attachment/")) {
                    String id = Uri.decode(path.substring("/attachment/".length()));
                    byte[] bytes = backend.attachmentBytes(id);
                    if (bytes == null) return null;
                    return new WebResourceResponse(backend.attachmentMediaType(id), null, new ByteArrayInputStream(bytes));
                }
            } catch (Exception ignored) {}
            return super.shouldInterceptRequest(view, request);
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if ("app.local".equals(uri.getHost()) && uri.getPath() != null && uri.getPath().startsWith("/export/")) {
                String[] parts = uri.getPath().split("/", 4);
                String kind = parts.length > 2 ? parts[2] : "json";
                String id = parts.length > 3 ? parts[3] : "";
                prepareExport(kind, id);
                return true;
            }
            return false;
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST) {
            Uri[] result = null;
            if (resultCode == RESULT_OK) {
                if (data != null && data.getClipData() != null) {
                    int count = data.getClipData().getItemCount();
                    result = new Uri[count];
                    for (int i = 0; i < count; i++) result[i] = data.getClipData().getItemAt(i).getUri();
                } else if (data != null && data.getData() != null) result = new Uri[]{data.getData()};
                else if (pendingCameraUri != null) result = new Uri[]{pendingCameraUri};
            }
            if (fileCallback != null) fileCallback.onReceiveValue(result);
            fileCallback = null;
            pendingCameraUri = null;
            return;
        }
        if (requestCode == EXPORT_REQUEST && resultCode == RESULT_OK && data != null && data.getData() != null && pendingExportBytes != null) {
            try (OutputStream out = getContentResolver().openOutputStream(data.getData())) {
                if (out != null) out.write(pendingExportBytes);
                Toast.makeText(this, "Export gespeichert", Toast.LENGTH_SHORT).show();
            } catch (Exception error) {
                Toast.makeText(this, "Export fehlgeschlagen: " + error.getMessage(), Toast.LENGTH_LONG).show();
            }
            pendingExportBytes = null;
            pendingExportMime = null;
            pendingExportName = null;
        }
    }

    private void prepareExport(String kind, String resourceId) {
        try {
            String safeKind = kind == null ? "json" : kind;
            if ("attachment".equals(safeKind)) {
                byte[] bytes = backend.attachmentBytes(resourceId);
                if (bytes == null) throw new IllegalArgumentException("Anhang nicht gefunden");
                startExport(bytes, backend.attachmentMediaType(resourceId), "animal-health-" + resourceId);
                return;
            }
            if ("animal_pdf".equals(safeKind)) {
                startExport(animalPdf(resourceId), "application/pdf", "animal-health-" + resourceId + "-gesundheit.pdf");
                return;
            }
            if ("group_pdf".equals(safeKind)) {
                startExport(groupPdf(resourceId), "application/pdf", "animal-health-" + resourceId + "-gruppe.pdf");
                return;
            }
            if ("backup".equals(safeKind)) {
                startExport(backupZip(), "application/zip", "animal-health-backup.zip");
                return;
            }
            startExport(backend.exportJson().getBytes(StandardCharsets.UTF_8), "application/json", "animal-health.json");
        } catch (Exception error) {
            Toast.makeText(this, "Export fehlgeschlagen: " + error.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void startExport(byte[] bytes, String mime, String name) {
        pendingExportBytes = bytes;
        pendingExportMime = mime;
        pendingExportName = name;
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType(mime == null ? "application/octet-stream" : mime);
        intent.putExtra(Intent.EXTRA_TITLE, name);
        startActivityForResult(intent, EXPORT_REQUEST);
    }

    private byte[] backupZip() throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ZipOutputStream zip = new ZipOutputStream(bytes, StandardCharsets.UTF_8)) {
            zip.putNextEntry(new ZipEntry("animal_health.json"));
            zip.write(backend.exportJson().getBytes(StandardCharsets.UTF_8));
            zip.closeEntry();
            try (Cursor c = backend.getReadableDatabase().rawQuery("SELECT id,filename,content FROM attachments ORDER BY id", null)) {
                while (c.moveToNext()) {
                    String filename = sanitizeFilename(c.getString(1));
                    zip.putNextEntry(new ZipEntry("attachments/AT-A" + c.getLong(0) + "-" + filename));
                    zip.write(c.getBlob(2));
                    zip.closeEntry();
                }
            }
        }
        return bytes.toByteArray();
    }

    private byte[] animalPdf(String animalId) throws Exception {
        JSONObject detail = new JSONObject(backend.handle(new JSONObject().put("type", "animal_health/animal_detail").put("animal_id", animalId).toString()));
        if (detail.has("__error")) throw new IllegalArgumentException(detail.getString("__error"));
        JSONObject animal = detail.getJSONObject("animal");
        List<String> lines = new ArrayList<>();
        lines.add("Stammdaten");
        addLine(lines, "Name", animal.optString("name"));
        addLine(lines, "Tierart", animal.optString("species"));
        addLine(lines, "Rasse", value(animal, "breed"));
        addLine(lines, "Farbe", value(animal, "color"));
        addLine(lines, "Geschlecht", value(animal, "sex"));
        addLine(lines, "Geburtsdatum", value(animal, "birth_date"));
        addLine(lines, "Tiergruppe", value(animal, "group_name"));
        lines.add(""); lines.add("Aktuell laufende Aufgaben / Serien");
        JSONArray tasks = detail.optJSONArray("tasks");
        if (tasks != null) for (int i=0;i<tasks.length();i++) { JSONObject t=tasks.getJSONObject(i); if (t.optBoolean("is_active", true)) lines.add("• " + t.optString("title") + " · " + t.optString("recurrence_type", "once")); }
        lines.add(""); lines.add("Gesundheitschronik – neuester Eintrag zuerst");
        JSONArray events = detail.optJSONArray("events");
        if (events != null) for (int i=0;i<events.length();i++) { JSONObject e=events.getJSONObject(i); String value=e.isNull("value")?"":(" · "+e.opt("value")+" "+value(e,"unit")); lines.add("• " + e.optString("occurred_at") + " · " + e.optString("title") + value + (value(e,"notes").isBlank()?"":" · "+value(e,"notes"))); }
        byte[] profile = null;
        String profileId = value(animal, "profile_image_id");
        if (!profileId.isBlank()) profile = backend.attachmentBytes(profileId);
        return makePdf("Animal Health – " + animal.optString("name"), lines, profile);
    }

    private byte[] groupPdf(String groupId) throws Exception {
        JSONObject features = new JSONObject(backend.handle(new JSONObject().put("type","animal_health/features").toString()));
        JSONObject state = new JSONObject(backend.handle(new JSONObject().put("type","animal_health/v081/state").toString()));
        String name = groupId; JSONArray groups=features.optJSONArray("groups");
        if(groups!=null)for(int i=0;i<groups.length();i++){JSONObject g=groups.getJSONObject(i);if(groupId.equals(g.optString("id"))){name=g.optString("name",groupId);break;}}
        List<String> lines=new ArrayList<>();lines.add("Tiergruppe: "+name);lines.add("");lines.add("Gruppenchronik – neuester Eintrag zuerst");JSONArray events=state.optJSONArray("group_events");int count=0;if(events!=null)for(int i=0;i<events.length();i++){JSONObject e=events.getJSONObject(i);if(!groupId.equals(e.optString("group_id")))continue;lines.add("• "+e.optString("occurred_at")+" · "+e.optString("title")+(value(e,"notes").isBlank()?"":" · "+value(e,"notes")));count++;}if(count==0)lines.add("Keine Einträge.");return makePdf("Animal Health – "+name,lines,null);
    }

    private byte[] makePdf(String title, List<String> sourceLines, byte[] profileBytes) throws Exception {
        PdfDocument document = new PdfDocument(); Paint titlePaint=new Paint(Paint.ANTI_ALIAS_FLAG);titlePaint.setTextSize(20);titlePaint.setFakeBoldText(true);Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);paint.setTextSize(10);int pageNumber=1,y=48;PdfDocument.Page page=document.startPage(new PdfDocument.PageInfo.Builder(595,842,pageNumber).create());Canvas canvas=page.getCanvas();canvas.drawText(title,36,y,titlePaint);y+=28;
        if(profileBytes!=null){Bitmap bitmap=BitmapFactory.decodeByteArray(profileBytes,0,profileBytes.length);if(bitmap!=null){float scale=Math.min(100f/bitmap.getWidth(),100f/bitmap.getHeight());canvas.drawBitmap(bitmap,null,new android.graphics.RectF(36,y,36+bitmap.getWidth()*scale,y+bitmap.getHeight()*scale),paint);y+=110;bitmap.recycle();}}
        for(String raw:sourceLines){for(String line:wrap(raw,92)){if(y>805){document.finishPage(page);pageNumber++;page=document.startPage(new PdfDocument.PageInfo.Builder(595,842,pageNumber).create());canvas=page.getCanvas();y=42;}canvas.drawText(line,36,y,paint);y+=15;}}
        document.finishPage(page);ByteArrayOutputStream out=new ByteArrayOutputStream();document.writeTo(out);document.close();return out.toByteArray();
    }

    private static List<String> wrap(String text,int width){List<String> out=new ArrayList<>();String value=text==null?"":text;if(value.length()<=width){out.add(value);return out;}int start=0;while(start<value.length()){int end=Math.min(value.length(),start+width);if(end<value.length()){int space=value.lastIndexOf(' ',end);if(space>start+20)end=space;}out.add(value.substring(start,end).trim());start=end;while(start<value.length()&&value.charAt(start)==' ')start++;}return out;}
    private static void addLine(List<String> lines,String label,String value){if(value!=null&&!value.isBlank())lines.add(label+": "+value);}
    private static String value(JSONObject object,String key){if(object==null||!object.has(key)||object.isNull(key))return"";return String.valueOf(object.opt(key));}
    private static String sanitizeFilename(String name){String value=name==null||name.isBlank()?"document":name;return value.replaceAll("[\\\\/:*?\"<>|]","_");}
}
