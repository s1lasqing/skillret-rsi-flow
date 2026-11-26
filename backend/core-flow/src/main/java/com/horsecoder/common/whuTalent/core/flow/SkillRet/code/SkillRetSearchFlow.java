package com.horsecoder.common.whuTalent.core.flow.SkillRet.code;

import cc.eamon.open.flow.core.FlowEngine;
import cc.eamon.open.flow.core.stereotype.Flow;
import cc.eamon.open.flow.spring.FlowComponent;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.Proxy;
import java.net.URL;

@FlowComponent
public class SkillRetSearchFlow {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String SEARCH_URL = "http://127.0.0.1:18940";

    @Flow("SKILLRET_SEARCH_WHOLE")
    public void whole(String queryId, String variant) throws IOException {
        if (!"A".equals(variant) && !"B".equals(variant)) {
            throw new IllegalArgumentException("Select A or B.");
        }
        String result = search(queryId, "whole", "wholeJson");
        FlowEngine.instance().register("branchCount", JSON.readTree(result).path("branchCount").asInt());
        FlowEngine.instance().register("mode", "A".equals(variant) ? 0 : 1);
    }

    @Flow("SKILLRET_SEARCH_BRANCH_ONE")
    public void first(String queryId) throws IOException {
        search(queryId, 0, "firstJson");
    }

    @Flow("SKILLRET_SEARCH_BRANCH_TWO")
    public void second(String queryId) throws IOException {
        search(queryId, 1, "secondJson");
    }

    @Flow("SKILLRET_SEARCH_BRANCH_THREE")
    public void third(String queryId) throws IOException {
        search(queryId, 2, "thirdJson");
    }

    @Flow("SKILLRET_SEARCH_COMPARE")
    public void compare(String queryId, String variant, String wholeJson,
                        String firstJson, String secondJson, String thirdJson) throws IOException {
        ObjectNode request = JSON.createObjectNode();
        request.put("queryId", queryId);
        request.put("variant", variant);
        request.set("whole", JSON.readTree(wholeJson));
        ArrayNode branches = request.putArray("branches");
        if ("B".equals(variant)) {
            for (String stage : new String[] {firstJson, secondJson, thirdJson}) {
                if (stage != null) {
                    branches.add(JSON.readTree(stage));
                }
            }
        }
        FlowEngine.instance().register("result", post("/score", request));
    }

    private static String search(String queryId, Object branch, String resultKey) throws IOException {
        ObjectNode request = JSON.createObjectNode().put("queryId", queryId);
        request.set("branch", JSON.valueToTree(branch));
        String result = post("/retrieve", request);
        FlowEngine.instance().register(resultKey, result);
        return result;
    }

    private static String post(String path, ObjectNode body) throws IOException {
        HttpURLConnection http = (HttpURLConnection) new URL(SEARCH_URL + path).openConnection(Proxy.NO_PROXY);
        try {
            http.setRequestMethod("POST");
            http.setConnectTimeout(3000);
            http.setReadTimeout(30000);
            http.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            http.setDoOutput(true);
            try (OutputStream output = http.getOutputStream()) {
                output.write(JSON.writeValueAsBytes(body));
            }
            int status = http.getResponseCode();
            if (status != 200) {
                throw new IOException("Local retrieval returned HTTP " + status);
            }
            try (InputStream input = http.getInputStream()) {
                return JSON.readTree(input).toString();
            }
        } finally {
            http.disconnect();
        }
    }
}

