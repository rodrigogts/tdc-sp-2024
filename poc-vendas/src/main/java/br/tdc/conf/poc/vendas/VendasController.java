package br.tdc.conf.poc.vendas;

import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import lombok.extern.slf4j.Slf4j;

import java.util.Random;

@Slf4j
@Path("/api/")
public class VendasController {

    private Random random = new Random();

    @GET
    @Path("ping")
    @Produces(MediaType.TEXT_PLAIN)
    public Response ping(){
        return Response.ok("pong").build();
    }

    @GET
    @Path("venda")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response registrarVenda() {
        if (random.nextInt(100) < 10) {
            throw new RuntimeException("Falha ao processar venda");
        }

        return Response.ok("Venda processada com sucesso").build();
    }
}
